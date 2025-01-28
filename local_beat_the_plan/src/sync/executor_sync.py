import math
import random
import sys

from src.sync.grammar_sync import SynCParser, SYNC_AST_CHILDREN_INDEXES, get_char_of_node, get_line_of_node
from src.sync.execution_exceptions import *
from src.sync.precompiled_grammar_sync import PRECOMPILED_GRAMMAR
from src.sync.converter_sync import *
from collections import defaultdict


def check_is_string_is_ascii_printable_with_escape(s):
    """
    Vérifie si tous les caractères de s sont ascii et affichable (nombre, lettres, ponctuation ou espace) ou des
    caractères échappés ASCII (\n, \r, \t, \v, \f, \0,, \' et \\)
    :param s:
    :return: L'indice du premier caractère qui ne vérifie pas cette propriété ou None si la chaîne est correcte.
    """
    check_escape = False
    for i, c in enumerate(s):
        if not check_escape and c == '\\':
            check_escape = True
            continue
        elif check_escape:
            if c in "0tvrnf\\'":
                check_escape = False
                continue
        elif 32 <= ord(c) <= 126:
            continue

        return i


class SynCProgram:
    """
    Classe qui représente un programme SYNC en train d'être exécuté
    """
    def __init__(self, tree):
        """
        :param tree: Arbre syntaxique abstrait du programme.
        """

        # Pour chaque structure, associe le nom de cette structure au nom de ses champs, dans l'ordre
        # Cette information, bien que non nécessaire pour l'exécution du code est utilisée pour comprendre les erreurs
        # de compilation en détaillant, par exemple pour le cas où deux structures auraient le même champs.
        self.structures_fields = dict()

        # Pour chaque champs de chaque structure un entier correspondant à sa position dans sa structure
        # La première position est 0
        # Deux structures ne peuvent avoir un champs en commun mais deux champs différents de deux structures différentes
        # peuvent avoir une position commune
        self.structures_fields_indexes = dict()

        # Pour chaque fonction, associe le nom de cette fonction à un dictionnaire contenant :
        # - la liste des noms de ses paramètres (associée à la clef 'parameters')
        # - son arbre syntaxique (associé à la clef 'tree')
        self.functions_infos = dict()

        # Pour chaque chaîne de caractère, associe la chaîne à son adresse dans la mémoire du programme.
        self.read_only_strings_adress = dict()

        # Mémoire interne du programme
        # Cette mémoire ne contient que des mots de 32 bits (donc des entiers entre 0 et 2**24-1)
        # Il s'agit d'un dictionnaire qui associe à chaque adresse un mot. Les adresses vont de 1 à 2**24 - 1
        # La valeur par défaut d'une case est 0.
        self.memory = defaultdict(int)

        # Adresse en dessous de laquelle les cases de la mémoire sont en lecture seule, on ne peut pas modifier la mémoire
        # Cela arrive pour les chaînes de caractère qui sont écrites en dur dans le code.
        # La case numéro self.read_write_stack_limit n'est pas en lecture seule.
        self.read_write_stack_limit = 1

        # Tas de la mémoire interne du programme
        # Cette mémoire contient des pointeurs, tableaux et structures créées avec MALLOC et MALLOC_STRUCT
        # Il s'agit d'une liste contenant des tuples (addresse, nombre de case réservée). Ces tuples sont triés dans
        # l'ordre inverse des adresses. La première adresse alouée est la dernière adresse accessible.
        self.memory_heap = []

        # Variables globales
        # L'addresse d'une variable globale est self.read_write_stack_limit + le nombre de variables globales
        # déclarées avant.
        self.global_variables = []

        # Pile des variables locales. La dernière liste contient les noms des variables locales de la fonction en cours
        # Puisque toute variable est codée sur le même nombre de bits, l'adresse de la variable est
        # (self.read_write_stack_limit + len(self.global_variables) + le nombre de variables déclarées avant).
        self.local_variables = []

        # Liste des caractères qui ont été lus lors de l'appel à la fonction READ mais qui n'ont pas encore été utilisés
        self.input_buffer = []

        # Nombre d'opérations élémentaires effectuées depuis le début de l'exécution du programme
        self.nb_elementary_operations = 0

        # Objet pour l'aléatoire
        self.random = random.Random()

        # On lit les fonctions et les structures
        self._read_structs_and_functions(tree)

        # On recherche toutes les chaînes de caractères statiques
        self._search_for_static_strings(tree)

        # On vérifie que les entiers, char et flottants écrits en durs sont bien écrits
        self._search_int_char_float_errors(tree)

        # On déclare et définit les variables globales
        self._declare_globals(tree)

        # On vérifie que le programme possède une fonction main sans paramètre d'entrée
        self._check_main_function()

    def _get_memory(self, address, line=None, char=None):
        """
        Renvoie le mot binaire situé à l'adresse address.

        line et char indiquent des informations de la ligne et le caractère du programme où on a eu
         besoin d'accéder à cette adresse et servent en cas d'exception (mauvais accès à la mémoire),
        """
        if address <= 0 or address >= MEMORY_SIZE:
            raise MemoryAccessError(line, char, address)
        return self.memory[address]

    def _set_memory(self, address, value, line=None, char=None):
        """ Remplace le mot situé à l'adresse address par la valeur value.

        line et char indiquent des informations de la ligne et le caractère du programme où on a eu
         besoin d'accéder à cette adresse et servent en cas d'exception (mauvais accès à la mémoire),
         """

        # On ne peut accéder à une adresse négative ou nulle ou supérrieure à la taille de la mémoire
        if address <= 0 or address >= MEMORY_SIZE:
            raise MemoryAccessError(line, char, address)

        # On ne peut modifier la mémoire correspondant aux chaînes de caractères statiques, en dessous de
        # l'adresse self.read_write_stack_limit
        if address < self.read_write_stack_limit:
            raise ReadOnlyMemoryWriteError(line, char, address)

        # On modifie la mémoire
        self.memory[address] = value

    def _check_memory_limit_exceeded(self, address=None):
        """
        Renvoie vrai si l'adresse de la dernière varaible locale est strictement plus petite que address
        Si address est None, alors address est la première addresse réservée du tas. Si aucune adresse n'est réservée
        il s'agit de la taille de la mémoire.
        """
        local_variable_last_address = self.read_write_stack_limit + sum(len(l) for l in self.local_variables)

        if address is None:
            if len(self.memory_heap) == 0:
                address = MEMORY_SIZE
            else:
                address = self.memory_heap[-1][0]

        return local_variable_last_address < address

    def _malloc(self, size, line=None, char=None):
        """Recherche dans la mémoire s'il existe un endroit avec size cases libres successives.
        Il y a trois types de cases réservées dans la mémoire: les chaînes statiques, les variables locales de la pile
        et les cases réservées avec malloc. La mémoire ressemble au schémas suivant:

        -------------- Haut de la mémoire (adresse 2**24 - 1)
        Cases réservées avec malloc, mélangées avec des cases libres
        Cases libres
        Variables locales
        Chaînes statiques
        -------------- Bas de la mémoire (adresse 1)

        Pour trouver une zone, regarde la liste memory_heap des cases déjà réservées depuis le bas, on cherche si,
        parmi ces cases se trouvent size cases libres consécutives. Sinon, on regarde s'il y a size cases libres entre
        les cases réservées avec malloc et les variables locales.

        Une exception est levée si size est nul ou négatif.

        Renvoie la première des cases allouées.
        Renvoie NULL si aucune place libre n'est trouvée.
        """

        if size <= 0:
            raise MallocNegativeSizeError(line, char)

        # On parcours les addresses réservées
        if len(self.memory_heap) == 0:
            address = MEMORY_SIZE - size
            index_in_heap = 0
        else:
            previous_address = MEMORY_SIZE
            for index, (reserved_address, reserved_size) in enumerate(self.memory_heap):
                # On regarde si on peut insérer les size cases entre le pointeur d'adresse reserved_address et de taille
                # reserved_size et le pointeur précédent
                if reserved_address + reserved_size + size < previous_address:
                    # Si oui, on a trouvé un emplacement, on s'arrête de chercher
                    address = reserved_address + reserved_size
                    index_in_heap = index
                    break
                previous_address = reserved_address
            else:
                # Pas de place dans les cases libres mélangées aux cases réservées, on va donc réserver des cases
                # dans les cases libres entre les variables locales et les cases réservées
                reserved_address, _ = self.memory_heap[-1]
                address = reserved_address - size
                index_in_heap = len(self.memory_heap)

        if not self._check_memory_limit_exceeded(address):
            return pointer_to_bin(NULL_ADDRESS)

        self.memory_heap.insert(index_in_heap, (address, size))
        return address

    def _free(self, pointer, line=None, char=None):
        """
        Libère la mémoire alouée pour l'adresse pointée par pointer.

        Si ce pointeur n'a pas été alloué avec _malloc, lève une exception.
        """
        for i, (address, _) in enumerate(self.memory_heap):
            if address == pointer:
                del self.memory_heap[i]
                break
        else:
            raise FreeNotAllocatedPointer(line, char)

    def _get_variable_address(self, variable_name, line=None, char=None):
        """
        Renvoie l'adresse de la variable globale ou locale nommée variable_name

        Il doit s'agir d'une variable globale ou une variable locale associée à la fonction en cours d'exécution.
        """

        # Avant cette variable se trouvent dans la mémoire :
        # - les cases en lecture seule. La première case qui n'est pas en lecture seule est la case
        # self.read_write_stack_limit
        # - les autres variables globales si elle est globale ; toutes les variables globales sinon
        # - les variables locales des autres fonctions en attente, si elle est locale
        # soit la somme des taille de self.local_variables[i] pour i entre 0 et n - 2 où n est le nombre de fonctions
        # en cours d'exécution
        # - les variables locales de la fonction déclarées avant variable_name si elle est locale

        address = self.read_write_stack_limit
        try:
            # On regarde si c'est une variable globale et son indice dans la liste des variables globales
            index = self.global_variables.index(variable_name)
            address += index
        except ValueError:
            # C'est nécessairement une variable locale
            address += len(self.global_variables) + sum(len(lv) for lv in self.local_variables[:-1])
            try:
                index = self.local_variables[-1].index(variable_name)
                address += index
            except ValueError:
                # La variable n'est ni locale ni globale
                raise UndeclaredVariableError(line, char, variable_name)

        return address

    def _get_string_from_address(self, address, line=None, char=None):
        """
        Renvoie la chaîne de caractère enregistrée en mémoire à l'adresse address.
        La chaîne se termine quand on lit le caractère '\0'

        line et char indiquent des informations de la ligne et le caractère du programme où on a eu
         besoin d'accéder à cette chaîne et servent en cas d'exception (mauvais accès
        à la mémoire),
        """
        s = ''
        while True:
            c = bin_to_char(self._get_memory(address, line=line, char=char), line=line, char=char)
            if c == '\0':
                return s
            s += c
            address += 1

    def _set_string_to_address(self, s, address, line=None, char=None):
        """
        Ecrit en mémoire la chaîne de caractère s à l'adresse address.

        line et char indiquent des informations de la ligne et le caractère du programme où on a eu
         besoin d'accéder à cette chaîne et servent en cas d'exception (mauvais accès
        à la mémoire),
        """

        # On commence par la dernière case pour provoquer directement une exception si on dépasse la dernière mémoire
        # lors de l'écriture. Cela évite d'attendre la dernière case si, par exemple, on a une chaîne de taille égale
        # à la taille de la mémoire.
        self._set_memory(address + len(s), char_to_bin('\0'), line=line, char=char)

        # On écrit ensuite toutes les autres cases.
        for i, c in enumerate(s):
            self._set_memory(address + i, char_to_bin(c), line=line, char=char)

    def _read_structs_and_functions(self, tree):
        """
        Parcours le programme pour trouver les déclaration est structures et des fonctions.
        Enregistre des informations utiles pur chacune

        Si deux structures ont le même nom, une exception est levée.
        Si deux fonctions ont le même nom, une exception est levée.
        Si deux structures ont un champs identique, une exception est levée.
        Si une structure a deux champs identiques, une exception est levée.
        Si une fonction a deux paramètres identiques, une exception est levée.
        """
        prog = tree[1]

        def _read_structure(structure):
            """
            Enregistre les informations utiles dans self.structures et self.structures_fields
            structure est l'arbre syntaxique abstrait de la déclaration de la structure.
            """

            # On lit le nom de la structure
            structure_name = structure[SYNC_AST_CHILDREN_INDEXES[SynCParser.structdecl]['struct_name']][1]

            # On récupère la ligne et la colonne en cas d'erreur
            node_line = get_line_of_node(structure)
            node_char = get_char_of_node(structure)

            # Une struture ne peut être déclarée qu'une fois
            if structure_name in self.structures_fields:
                raise SameNameStructureError(node_line, node_char, structure_name)

            # On lit les champs de la structure
            start, end, step = SYNC_AST_CHILDREN_INDEXES[SynCParser.structdecl]['fields']
            # On sait qu'il y a au moins un champs sinon la structure n'aurait pas été validée par la grammaire
            structure_fields = [field[1] for field in structure[start:end:step]]

            # On enregistre tout ça dans self.structures
            self.structures_fields[structure_name] = structure_fields

            # On enregistre les positions des champs
            for i, field in enumerate(structure_fields):
                # La structure ne peux avoir deux fois le même champs
                if field in structure_fields[i + 1:]:
                    raise SameFieldsNameStructureError(node_line, node_char, structure_name, field)

                # Le champs d'une structure ne peut apparaître dans une autre structure
                if field in self.structures_fields_indexes:
                    for other_structure_name, other_fields in self.structures_fields.items():
                        if other_structure_name == structure_name:
                            continue
                        if field in other_fields:
                            raise SameFieldStructureError(node_line, node_char,
                                                          other_structure_name, structure_name, field)

                self.structures_fields_indexes[field] = i

        def _read_function(function):
            """
            Enregistre les information utiles de la fonction dans self.functions_infos
            function est l'arbre syntaxique abstrait de la déclaration et définition de la fonction.
            """

            # On récupère le nom de la fonction
            function_name = function[SYNC_AST_CHILDREN_INDEXES[SynCParser.fundecl]['function_name']][1]

            # On récupère ses lignes et colonnes en cas d'erreur
            node_line = get_line_of_node(function)
            node_char = get_char_of_node(function)

            # Une fonction ne peut être déclarée deux fois
            if function_name in self.functions_infos:
                raise SameNameFunctionError(node_line, node_char, function_name)

            # On récupère ses paramètres
            start, end, step = SYNC_AST_CHILDREN_INDEXES[SynCParser.fundecl]['parameters']
            parameters = tuple(parameter[1] for parameter in function[start:end:step])

            # La fonction ne peut avoir deux fois le même paramètre
            for i, parameter in enumerate(parameters):
                if parameter in parameters[i + 1:]:
                    raise SameParametersNameFunctionError(node_line, node_char, function_name, parameter)

            # On enregistre les informations
            self.functions_infos[function[2][1]] = {
                'parameters': parameters,
                'tree': function[SYNC_AST_CHILDREN_INDEXES[SynCParser.fundecl]['block']],
                'line': node_line,
                'char': node_char
            }

        # Pour chaque élément déclaré dans le programme, on appelle la fonction adaptée
        for decl in prog[1:]:
            if decl[0] == SynCParser.structdecl:
                _read_structure(decl)
            elif decl[0] == SynCParser.fundecl:
                _read_function(decl)

    def _check_main_function(self):
        """
        Vérifie qu'il existe une fonction main et que cette fonction n'a pas de paramètre d'entrée.
        Une exception est levée dans le cas contraire.
         """

        # On vérifie que la fonction main a été déclarée
        if 'main' not in self.functions_infos:
            raise NoMainFunctionError()

        # On récupère les paramètes de la fonction main
        main_function = self.functions_infos['main']
        nb_params = len(main_function['parameters'])

        # S'il y a plus d'un paramètre, on renvoie une erreur
        if nb_params != 0:
            node_line = main_function['line']
            node_char = main_function['char']
            raise MainFunctionWithParametersError(node_line, node_char)

    def _search_for_static_strings(self, tree):
        """
        Parcours récursivement l'arbre syntaxique abstrait du programme pour retrouver toutes les chaînes statiques
        du programme. Ces chaînes sont enregistrée au début de la mémoire en lecture seule.

        Une exception est levée si les chaînes sont tellement longues qu'on dépasse la plage mémoire autorisée.
        """

        def _search_for_static_strings_aux(subtree):
            """Parcours récursivement subtree pour trouver les chaînes statiques"""

            # Si le noeud en cours n'est pas un tuple, c'est une feuille
            # Et si c'est une feuille ce n'est pas une chaîne de caractère (car on la capture au niveau du tuple qui
            # qui la contient
            if type(subtree) is not tuple:
                pass
            # Si c'est une chaîne de caractère ...
            elif subtree[0] == SynCParser.T.string:

                # On récupère la ligne et la colonne de la chaîne en cas d'exception
                node_line = get_line_of_node(subtree)
                node_char = get_char_of_node(subtree)

                # On récupère la valeur de la chaîne
                string_value = subtree[1][1:-1]

                # Si la chaîne existe déjà dans la mémoire, on ne fait rien
                # Il n'est pas nécessaire d'enregistrer deux fois la valeur
                if string_value in self.read_only_strings_adress:
                    return
                self.read_only_strings_adress[string_value] = self.read_write_stack_limit

                # On vérifie que la chaîne est en ASCII et les caractères échappés
                error_char_index = check_is_string_is_ascii_printable_with_escape(string_value)
                if error_char_index is not None:
                    node_char += error_char_index + 1
                    raise NonValidCharacterError(node_line, node_char, string_value[error_char_index])

                # Le decode et encode permet de gérer les échappement de caractère
                # Par exemple si l'utilisateur a rentré la chaîne "abc\n"
                # L'exécuteur la reçoit sous la forme échapée : "abc\\n"
                # Il faut donc supprimer l'échappement, c'est ce que fait la ligne suivante
                string_value = string_value.encode().decode('unicode_escape')

                # On enregistre la chaîne
                self._set_string_to_address(string_value, self.read_write_stack_limit, line=node_line, char=node_char)

                # On met à jour l'adresse en dessous de laquelle on ne peut rien modifier (car les chaînes de caractère écrite
                # en dur sont en lecture seule.
                self.read_write_stack_limit += len(string_value) + 1

            # Sinon on continue récursivement
            else:
                for subsubtree in subtree[1:]:
                    _search_for_static_strings_aux(subsubtree)

        _search_for_static_strings_aux(tree)

    def _search_int_char_float_errors(self, tree):
        """ Cette fonction parcours tout l'arbre et vérifie si les entiers, flottant et charactères écrits en dur dans
        le code sont encodables. Par exemple l'entier 1234567891234 n'est pas encodage avec 32 bits.

        Une exception est levée dans le cas contraire.
        """

        def _search_for_int_char_float_errors_aux(subtree):
            # Si le noeud en cours n'est pas un tuple, c'est une feuille
            # Et si c'est une feuille ce n'est pas une chaîne de caractère (car on la capture au niveau du tuple qui
            # qui la contient
            if type(subtree) is not tuple:
                pass
            # Si c'est un entier, on vérifie qu'il est dans la bonne plage
            elif subtree[0] == SynCParser.T.integer:
                intval = int(subtree[1])
                node_line = get_line_of_node(subtree)
                node_char = get_char_of_node(subtree)
                if -2**31 <= intval < 2**31:
                    return
                raise NonValidIntegerError(node_line, node_char, subtree[1])

            # Si c'est un caractère, on fait la même vérification que pour les chaînes
            # C'est nécessairement une chaîne avec un unique caractère ou deux caractères représentant un caractère
            # échappé
            elif subtree[0] == SynCParser.T.char:
                c = subtree[1][1:-1]
                error_char_index = check_is_string_is_ascii_printable_with_escape(c)
                if error_char_index is not None:
                    node_line = get_line_of_node(subtree)
                    node_char = get_char_of_node(subtree) + error_char_index + 1
                    raise NonValidCharacterError(node_line, node_char, c)

            # Si c'est un flottant on ne fait rien
            elif subtree[0] == SynCParser.T.floatn:
                pass

            # Sinon on continue récursivement
            else:
                for subsubtree in subtree[1:]:
                    _search_for_int_char_float_errors_aux(subsubtree)

        _search_for_int_char_float_errors_aux(tree)

    def _declare_globals(self, tree):

        prog = tree[1]

        # On vérifie s'il y a des variables globales
        if prog[1][0] != SynCParser.globalsdecl:
            return

        globals_declaration = prog[1]
        start, end, step = SYNC_AST_CHILDREN_INDEXES[SynCParser.globalsdecl]['global_variables']
        for global_affect in globals_declaration[start:end:step]:

            variable = global_affect[SYNC_AST_CHILDREN_INDEXES[SynCParser.globalaffect]['variable']][1]
            value_literal = global_affect[SYNC_AST_CHILDREN_INDEXES[SynCParser.globalaffect]['value']]

            # On récupère la ligne et la colonne de l'affectation en cas d'erreur
            node_line = get_line_of_node(global_affect)
            node_char = get_char_of_node(global_affect)

            if variable in self.global_variables:
                raise SameGlobalVariableNameError(node_line, node_char, variable)

            # On vérifie qu'aucune fonction ne déclare en paramètre une variable du même nom que la variable globale
            for function_name in self.functions_infos:
                parameters = self.functions_infos[function_name]['parameters']
                if variable in parameters:
                    raise GlobalVariableAndFunctionParameterWithSameNameError(node_line, node_char, variable, function_name)

            self.global_variables.append(variable)

            # On récupère la valeur de la variable. On a déjà lu toutes les chaînes statique, char et entiers pour
            # vérifier leur validité.

            if value_literal[0] == SynCParser.T.integer:
                value = int_to_bin(int(value_literal[1]))
            elif value_literal[0] == SynCParser.T.floatn:
                value = float_to_bin(float(value_literal[1]))
            elif value_literal[0] == SynCParser.T.char:
                value = char_to_bin(value_literal[1][1:-1])
            elif value_literal[0] == SynCParser.T.string:
                value = self.read_only_strings_adress[value_literal[1][1:-1]]
            elif value_literal[1] in ['NULL', 'TRUE', 'FALSE']:
                value = literal_to_bin(value_literal[1])
            else:
                # Ce cas ne devrait jamais se produire
                raise ExecutionError(node_line, node_char, "Unknown error CODE 0, contact developer")

            address = self._get_variable_address(variable, line=node_line, char=node_char)
            self._set_memory(address, value, line=node_line, char=node_char)

    def main_function_iterator(self):
        """
        Générateur qui, au cours des itérations, exécute le programme.
        Effectue un yield du dernier numéro de ligne et de caractère exécuté à chaque opération élémentaire.
        """
        for elementary, value, node_line, node_char in self.execute_function('main'):
            if elementary:
                self.nb_elementary_operations += 1
                yield node_line, node_char

    def execute_function(self, function_name, *params):
        """
        Itérateur qui exécute la fonction donnée en entrée.
        Cette fonction est une fonction non intégrée au langage (elle est déclarée et définie dans le programme)

        Pour chaque opération élémentaire ou non, l'itérateur effectue un yield,
        Chaque yield contient deux informations :
            un booléen indiquant si l'opération exécutée est élémentaire
            une valeur binaire si la fonction transfert ou renvoie un valeur
        La valeur peut être un tuple contenant la chaîne 'RETURN' suivie d'une valeur. Dans ce cas, il s'agit de la
        valeur de retour de la fonction elle même, une fois ce yield effectué, on cesse l'exécution de la fonction.

        params sont les valeurs binaires des paramètres d'entrée de la fonction, dans l'ordre.

        On suppose que le nombre de paramètres a déjà été vérifié, on suppose que la fonction a été déclarée.
        """

        # On récupère l'arbre syntaxique abstrait de la fonction

        tree = self.functions_infos[function_name]['tree']
        node_line = self.functions_infos[function_name]['line']
        node_char = self.functions_infos[function_name]['char']

        # On ajoute les variables locales de la fonction
        parameters = self.functions_infos[function_name]['parameters']
        self.local_variables.append(list(parameters))

        # On vérifie qu'on a pas dépassé la taille mémoire
        if not self._check_memory_limit_exceeded():
            raise MemoryExceededError(node_line, node_char, parameters[-1])

        if len(parameters) != 0:
            address0 = self._get_variable_address(parameters[0], line=node_line, char=node_char)
            for i, param in enumerate(params):
                self._set_memory(address0 + i, param, line=node_line, char=node_char)

        # On exécute la fonction, et on transfert toutes ses opérations élémentaires
        for elementary, value, node_line, node_char in self.execute_node(tree):
            # Si la valeur est non vide, on vérifie si c'est le rézsultat d'un RETURN
            # Dans ce cas, la valeur est un tuple contenant le mot RETURN et la valeur retournée
            # Et dans ce cas, on cesse toute autre exécution de la fonction
            if value is not None and type(value) is tuple and value[0] == 'RETURN':
                yield elementary, value[1], node_line, node_char
                break

            # Sinon on transfert l'opération
            yield elementary, value, node_line, node_char

        # On libère la mémoire des variables locales
        del self.local_variables[-1]

    def execute_node(self, node):
        """
        Itérateur qui énumère toutes les opérations élémentaire du sous-programme correspondant au noeud donné en entrée.

        Chaque yield contient deux informations :
            un booléen indiquant si l'opération exécutée est élémentaire ou non
            une valeur binaire qui correspond à une valeur de retour si cela a un sens ; ou rien si aucune valeur de
            retour n'est calculée par l'opération

            (par exemple pour une addition, il y a
            - toutes les opérations élémentaires ou non permettant de calculer les valeurs binaires des deux opérandes,
            chaque opération élémentaire effectue un yield True, None et chaque opération
            non élémentaire effectue  un yield False, None
            - et une opération élémentaire qui renvoie le résultat de la somme  yield True, resultat

        Lève une exception en cas de problème lors de l'exécution (voir chaque sous-fonction pour plus de détails)
        """

        # On récupère la ligne et la colonne du noeud en cas d'exception
        node_line = get_line_of_node(node)
        node_char = get_char_of_node(node)

        # On effectue ensuite une fonction différente en fonction du noeud à exécuter.
        # Le but est juste d'éviter un gros if, on utilise un dictionnaire pour associer chaque type de noeud à
        # la bonne fonction.

        # Liste de toutes les fonctions

        def _execute_atom():
            """
            Exécute un atome (variable, entier, flottant, char, string, NULL, FALSE, TRUE, ...).

            Effecute un yield indiquant:
            - que ce n'est pas une opération élémentaire (False)
            - la valeur de l'atome (la valeur de la variable, ou la valeur du littéral)
            si c'est une chaîne de caractère, renvoie un pointeur vers son premier caractère.

            Les littéraux entiers et caractères sont nécessairement valides car on a déjà vérifié tous les entiers,
            et caractères du programme.


            """
            literal = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.atom]['literal']]

            # Si c'est une variable, on récupère sa valeur
            if literal[0] == SynCParser.T.ident:
                variable = literal[1]
                address = self._get_variable_address(variable, line=node_line, char=node_char)
                value = self._get_memory(address, line=node_line, char=node_char)
            # Si c'est un entier, un flottant, un caractère, une chaîne de caractères ou un mot-clef littéral
            # On récupère la valeur correspondante
            # Le cas du pointeur n'est pas possible, toute opération donnant un pointeur ne donne pas un atome mais
            # un BINARY_KEYWORD ; la seule exception est le pointeur NULL ou une chaîne de caractère statique.
            elif literal[0] == SynCParser.T.integer:
                value = int_to_bin(int(literal[1]))
            elif literal[0] == SynCParser.T.floatn:
                value = float_to_bin(float(literal[1]))
            elif literal[0] == SynCParser.T.char:
                value = char_to_bin(literal[1][1:-1])
            elif literal[0] == SynCParser.T.string:
                value = self.read_only_strings_adress[literal[1][1:-1]]
            elif literal[1] in ['NULL', 'TRUE', 'FALSE']:
                value = literal_to_bin(literal[1])
            else:
                # Ce cas ne devrait jamais se produire
                raise ExecutionError(node_line, node_char, "Unknown error CODE 1, contact developer")

            # On effecute un yield avec la valeur. Calculer la valeur d'un atome n'est pas une opération élémentaire
            yield False, value, node_line, node_char

        def _execute_affect():
            """
            Exécute une affectation.
            
            
            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer l'opérande de droite.
            
            Puis effectue un yield indiquant que 
            - que c'est une opération élémentaire
            - il n'y a pas de valeur de retour
            
            """
            variable = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.affect]['variable']][1]

            # Si la variable n'a pas été déclarée, la déclare
            if variable not in self.global_variables and variable not in self.local_variables[-1]:
                self.local_variables[-1].append(variable)

                # On vérifie qu'on a pas dépassé la taille mémoire
                if not self._check_memory_limit_exceeded():
                    raise MemoryExceededError(node_line, node_char, variable)

            address = self._get_variable_address(variable, line=node_line, char=node_char)
            # La déclaration d'une variable n'est pas une opération élémentaire. On ne fait pas de yield.

            expr = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.affect]['expr']]
            binary_value = None
            # On calcule l'expression à droite de l'égalité
            for elementary, value, subnode_line, subnode_char in self.execute_node(expr):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire pour l'égalité de droite
                if value is not None:
                    binary_value = value

            # On effectue l'affectation
            self._set_memory(address, binary_value, line=node_line, char=node_char)

            # On effectue un yield indiquant qu'on a fait une opération élémentaire, mais il n'y a pas de valeur de
            # retour
            yield True, None, node_line, node_char

        def _execute_arrayaffect():
            """
            Exécute une affectation de type tableau p[i] = x.
            
            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer p, puis i, puis x.
            
            Puis effectue un yield indiquant que 
            - que c'est une opération élémentaire 
            - il n'y a pas de valeur de retour
            """

            array = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.arrayaffect]['array']]
            binary_array = None
            # On calcule la valeur du pointeur correspondant au tableau
            for elementary, value, subnode_line, subnode_char in self.execute_node(array):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_array = value

            index = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.arrayaffect]['index']]
            binary_index = None
            # On calcule la valeur correspondant à l'indice
            for elementary, value, subnode_line, subnode_char in self.execute_node(index):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_index = value

            expr = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.arrayaffect]['expr']]
            binary_value = None
            # On calcule la valeur correspondant au membre de droite
            for elementary, value, subnode_line, subnode_char in self.execute_node(expr):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_value = value

            address = bin_to_pointer(binary_array, line=node_line, char=node_char)
            index_value = bin_to_int(binary_index)

            # On effectue l'affectation
            self._set_memory(address + index_value, binary_value, line=node_line, char=node_char)

            # On effectue un yield indiquant qu'on a fait une opération élémentaire, mais il n'y a pas de valeur de
            # retour
            yield True, None, node_line, node_char

        def _execute_structaffect():
            """
            Exécute une affectation de type structure x->y = z.
            
            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer x, puis z.
            On ne calcule pas y car il s'agit d'un identifiant. 
            
            Puis effectue un yield indiquant que 
            - que c'est une opération élémentaire 
            - il n'y a pas de valeur de retour
            """

            struct = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.structaffect]['struct']]
            binary_struct = None
            # On calcule la valeur du pointeur correspondant au struct
            for elementary, value, subnode_line, subnode_char in self.execute_node(struct):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_struct = value

            # On récupère le nom du champs
            field = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.structaffect]['field']][1]

            expr = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.structaffect]['expr']]
            binary_value = None
            # On calcule la valeur correspondant au membre de droite
            for elementary, value, subnode_line, subnode_char in self.execute_node(expr):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_value = value

            address = bin_to_pointer(binary_struct, line=node_line, char=node_char)

            # On récupère l'indice du champs dans la structure correspondante.
            try:
                field_index = self.structures_fields_indexes[field]
            except KeyError:
                raise UndeclaredFieldError(node_line, node_char, field)

            # On effectue l'affectation
            self._set_memory(address + field_index, binary_value, line=node_line, char=node_char)

            # On effectue un yield indiquant qu'on a fait une opération élémentaire, mais il n'y a pas de valeur de
            # retour
            yield True, None, node_line, node_char

        def _execute_derefaffect():
            """
            Exécute une affectation de type structure *p = x.
            
            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer p, puis x.
            
            Puis effectue un yield indiquant que 
            - que c'est une opération élémentaire 
            - il n'y a pas de valeur de retour
            """
            pointer = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.derefaffect]['pointer']]
            binary_pointer = None
            # On calcule la valeur du pointeur
            for elementary, value, subnode_line, subnode_char in self.execute_node(pointer):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_pointer = value

            expr = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.derefaffect]['expr']]
            binary_value = None
            # On calcule la valeur correspondant au membre de droite
            for elementary, value, subnode_line, subnode_char in self.execute_node(expr):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_value = value

            address = bin_to_pointer(binary_pointer, line=node_line, char=node_char)
            # On effectue l'affectation
            self._set_memory(address, binary_value, line=node_line, char=node_char)

            # On effectue un yield indiquant qu'on a fait une opération élémentaire, mais il n'y a pas de valeur de
            # retour
            yield True, None, node_line, node_char

        def _execute_bracketexpr():
            """
            Transfert les opérations nécessaires pour calculer une opération parenthèsée
            Il ne s'agit pas d'une opération élémentaire, les parenthèses servent juste à changer l'ordre des priorités
            des opérateurs. 
            """
            child = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.bracketexpr]['expr']]
            for elementary, value, subnode_line, subnode_char in self.execute_node(child):
                yield elementary, value, subnode_line, subnode_char

        def _execute_binaryoperator():
            """
            Exécute une opération binaire non booléene,, L op R où op est une opération arithmétique, 
            ou de comparaison.
            
            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer L, puis R. 
            
            Puis effectue un yield indiquant que 
            - que c'est une opération élémentaire 
            - qu'il y a une valeur de retour égale au résultat de l'opération
            """

            left_expr = node[SYNC_AST_CHILDREN_INDEXES[node[0]]['left_expr']]
            binary_left_value = None
            # On calcule la valeur correspondant au membre de gauche
            for elementary, value, subnode_line, subnode_char in self.execute_node(left_expr):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_left_value = value

            right_expr = node[SYNC_AST_CHILDREN_INDEXES[node[0]]['right_expr']]
            binary_right_value = None
            # On calcule la valeur correspondant au membre de droite
            for elementary, value, subnode_line, subnode_char in self.execute_node(right_expr):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_right_value = value

            operator = node[SYNC_AST_CHILDREN_INDEXES[node[0]]['operator']][1]

            if operator in ['+', '-', '/', '*', '%', '<=', '>=', '<', '>']:
                left_value = bin_to_int(binary_left_value)
                right_value = bin_to_int(binary_right_value)
                if operator == '+':
                    result = int_to_bin(left_value + right_value, overflow=True)
                elif operator == '-':
                    result = int_to_bin(left_value - right_value, overflow=True)
                elif operator == '*':
                    result = int_to_bin(left_value * right_value, overflow=True)
                elif operator == '/':
                    try:
                        result = int_to_bin(left_value // right_value, overflow=True)
                    except ZeroDivisionError:
                        raise MathDomainError(node_line, node_char, right_value)
                elif operator == '%':
                    try:
                        result = int_to_bin(left_value % right_value, overflow=True) # A priori, pas d'overflow possible
                    except ZeroDivisionError:
                        raise MathDomainError(node_line, node_char, right_value)
                elif operator == '<=':
                    result = bool_to_bin(left_value <= right_value)
                elif operator == '>=':
                    result = bool_to_bin(left_value >= right_value)
                elif operator == '<':
                    result = bool_to_bin(left_value < right_value)
                elif operator == '>':
                    result = bool_to_bin(left_value > right_value)
            elif operator in ['+.', '-.', '/.', '*.', '<=.', '>=.', '<.', '>.']:
                left_value = bin_to_float(binary_left_value)
                right_value = bin_to_float(binary_right_value)
                if operator == '+.':
                    result = float_to_bin(left_value + right_value)
                elif operator == '-.':
                    result = float_to_bin(left_value - right_value)
                elif operator == '*.':
                    result = float_to_bin(left_value * right_value)
                elif operator == '/.':
                    try:
                        result = float_to_bin(left_value / right_value)
                    except ZeroDivisionError:
                        raise MathDomainError(node_line, node_char, right_value)
                elif operator == '<=.':
                    result = bool_to_bin(left_value <= right_value)
                elif operator == '>=.':
                    result = bool_to_bin(left_value >= right_value)
                elif operator == '<.':
                    result = bool_to_bin(left_value < right_value)
                elif operator == '>.':
                    result = bool_to_bin(left_value > right_value)
            elif operator in ['==', '!=']:
                if operator == '==':
                    result = bool_to_bin(binary_left_value == binary_right_value)
                elif operator == '!=':
                    result = bool_to_bin(binary_left_value != binary_right_value)
            else:
                # Ce cas ne devrait jamais se produire
                raise ExecutionError(node_line, node_char, "Unknown error CODE 2, contact developer")

            # On effectue un yield indiquant qu'on a fait une opération élémentaire, avec sa valeur de retour
            yield True, result, node_line, node_char

        def _execute_boolbinaryoperator():
            """
            Exécute une opération binaire booléene,, L AND R ou L OR R
            
            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer L, puis, si nécessaire, 
            calcule R.
            
            Si l'opérateur est OR et L est vrai ; ou si l'opérateur est AND et L est faux, il n'est pas nécessaire
            de calculer R.  
            
            Puis effectue un yield indiquant que 
            - que c'est une opération élémentaire 
            - qu'il y a une valeur de retour égale au résultat de l'opération
            """
            
            left_expr = node[SYNC_AST_CHILDREN_INDEXES[node[0]]['left_expr']]
            binary_left_value = None
            # On calcule la valeur correspondant au membre de gauche
            for elementary, value, subnode_line, subnode_char in self.execute_node(left_expr):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_left_value = value

            operator = node[SYNC_AST_CHILDREN_INDEXES[node[0]]['operator']][1]
            left_value = bin_to_bool(binary_left_value, line=node_line, char=node_char)

            # Si l'opérateur est AND et que left_value est faux, alors le résultat est nécessairement faux
            # Si l'opérateur est OR et que left_value est vrai, alors le résultat est nécessairement vrai
            result = None
            if operator == 'AND':
                if not left_value:
                    result = False
            elif operator == 'OR':
                if left_value:
                    result = True
            else:
                # Ce cas ne devrait jamais se produire
                raise ExecutionError(node_line, node_char, "Unknown error CODE 3, contact developer")

            # Si le résultat est déjà calculé, on ne calcule pas l'opérande droite
            if result is None:
                right_expr = node[SYNC_AST_CHILDREN_INDEXES[node[0]]['right_expr']]
                binary_right_value = None
                # On calcule la valeur correspondant au membre de droite
                for elementary, value, subnode_line, subnode_char in self.execute_node(right_expr):
                    # On transfert si l'opération mais pas la valeur
                    yield elementary, None, subnode_line, subnode_char

                    # Si value est non vide, alors on a une valeur binaire
                    if value is not None:
                        binary_right_value = value

                # Si l'opérande droite a été calculé c'estque
                # - l'opérateur est AND et que le membre gauche est vrai
                # - l'opérateur est OR et que le membre gauche est faux
                # Dans les deux cas, le résultat est exactement la valeur de opérande droite.
                result = bin_to_bool(binary_right_value, line=node_line, char=node_char)
            # On effectue un yield indiquant qu'on a fait une opération élémentaire, avec sa valeur de retour
            yield True, result, node_line, node_char

        def _execute_unaryoperator():
            """
            Exécute une opération unaire, NOT x ou $ x
            
            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer x. 
            
            Puis effectue un yield indiquant que 
            - que c'est une opération élémentaire 
            - qu'il y a une valeur de retour égale au résultat de l'opération
            """
            expr = node[SYNC_AST_CHILDREN_INDEXES[node[0]]['expr']]
            binary_value = None
            # On calcule la valeur correspondant au membre de droite
            for elementary, value, subnode_line, subnode_char in self.execute_node(expr):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_value = value

            operator = node[SYNC_AST_CHILDREN_INDEXES[node[0]]['operator']][1]

            if operator == 'NOT':
                value = bin_to_bool(binary_value, line=node_line, char=node_char)
                result = bool_to_bin(not value)
            elif operator == '$':
                address = bin_to_pointer(binary_value, line=node_line, char=node_char)
                result = self._get_memory(address, line=node_line, char=node_char)
            else:
                # Ce cas ne devrait jamais se produire
                raise ExecutionError(node_line, node_char, "Unknown error CODE 4, contact developer")

            # On effectue un yield indiquant qu'on a fait une opération élémentaire, avec sa valeur de retour
            yield True, result, node_line, node_char

        def _execute_refexpr():
            """
            Exécute une opération de référence &x

            x est nécessairemente une variable, il n'y a pas d'expression à calculer.

            Puis effectue un yield indiquant que
            - que c'est une opération élémentaire
            - qu'il y a une valeur de retour égale au résultat de l'opération
            """
            variable_name = node[SYNC_AST_CHILDREN_INDEXES[node[0]]['variable']][1]

            address = self._get_variable_address(variable_name, line=node_line, char=node_char)
            result = pointer_to_bin(address)

            # On effectue un yield indiquant qu'on a fait une opération élémentaire, avec sa valeur de retour
            yield True, result, node_line, node_char

        def _execute_call():
            """
            Exécute un appel de fonction prédéfinie ou non F(x1, x2, ..., xn)

            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer chaque paramètre xi.

            Puis effectue un yield indiquant que
            - que c'est une opération élémentaire
            - qu'il y a une valeur de retour égale au résultat de l'opération

            Renvoie une exception si la fonction n'a pas été déclarée et qu'elle n'est pas prédéfinie, si le nombre de
            paramètre est incorrect
            """

            function_name = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.call]['function_name']][1]

            # On calcule chaque valeur de paramètre
            start, end, step = SYNC_AST_CHILDREN_INDEXES[SynCParser.call]['parameters']
            parameters = node[start:end:step]

            if function_name in ['READ', 'RAND', 'FLUSH', 'FLUSHERR']:
                expected_nb_parameters = len(parameters) == 0
            elif function_name in ['IABS', 'FABS', 'COS', 'SIN', 'TAN', 'SQRT', 'EXP', 'LN', 'SH', 'CH', 'TH', 'CEIL',
                                       'FLOOR', 'ROUND', 'MALLOC_STRUCT', 'FREE', 'SRAND', 'I2F',
                                       'F2I', 'S2I', 'S2F', 'V2B', 'ELEMENTARY_OPERATIONS']:
                expected_nb_parameters = len(parameters) == 1
            elif function_name in ['POW']:
                expected_nb_parameters = len(parameters) == 2
            elif function_name in ['I2S', 'F2S']:
                expected_nb_parameters = len(parameters) == 3
            elif function_name in ['PRINT', 'PRINTERR']:
                expected_nb_parameters = True
            elif function_name == 'MALLOC':
                expected_nb_parameters = len(parameters) >= 1
            else:
                # Si la fonction n'a pas été déclarée, on envoie une exception
                if function_name not in self.functions_infos:
                    raise UndeclaredFunctionError(node_line, node_char, function_name)
                expected_nb_parameters = len(parameters) == len(self.functions_infos[function_name]['parameters'])

            if not expected_nb_parameters:
                raise IncorrectNumberOfParametersInFunction(node_line, node_char, function_name)

            binary_parameters = []

            # Cas spécial du MALLOC_STRUCT qui accepte des paramètres correspondant à des identifiants
            if function_name == 'MALLOC_STRUCT':
                binary_parameters.append(parameters[0][1][1])
            else:
                for parameter in parameters:
                    # Cas spécial du PRINT et PRINTERR qui acceptent des paramètres spéciaux
                    if parameter[1] in ['INT', 'FLOAT', 'CHAR', 'BOOL', 'STRING', 'POINTER']:
                        binary_parameters.append(parameter[1])
                        continue

                    binary_value = None
                    # On calcule la valeur correspondant au paramètre
                    for elementary, value, subnode_line, subnode_char in self.execute_node(parameter):
                        # On transfert si l'opération mais pas la valeur
                        yield elementary, None, subnode_line, subnode_char

                        # Si value est non vide, alors on a une valeur binaire
                        if value is not None:
                            binary_value = value
                    binary_parameters.append(binary_value)

            # Par défaut une fonction renvoie 0
            result = int_to_bin(0)
            if function_name in ['FABS', 'COS', 'SIN', 'TAN', 'SQRT', 'EXP', 'LN', 'SH', 'CH', 'TH', 'CEIL',
                                 'FLOOR', 'ROUND']:
                # Fonction mathématiques à 1 paramètre flottant
                value = bin_to_float(binary_parameters[0])
                if function_name == 'FABS':
                    # Fonction qui renvoie la valeur absolue d'un flottant
                    result = float_to_bin(abs(value))
                elif function_name == 'COS':
                    # Fonction qui renvoie le cosinus
                    result = float_to_bin(math.cos(value))
                elif function_name == 'SIN':
                    # Fonction qui renvoie le sinus
                    result = float_to_bin(math.sin(value))
                elif function_name == 'TAN':
                    # Fonction qui renvoie la tangente
                    result = float_to_bin(math.tan(value))
                elif function_name == 'SQRT':
                    # Fonction qui renvoie la racine carrée
                    try:
                        result = float_to_bin(math.sqrt(value))
                    except ValueError:
                        raise MathDomainError(node_line, node_char, value)
                elif function_name == 'EXP':
                    # Fonction qui renvoie l'exponentielle
                    result = float_to_bin(math.exp(value))
                elif function_name == 'LN':
                    # Fonction qui renvoie le logarighme népérien
                    try:
                        result = float_to_bin(math.log(value))
                    except ValueError:
                        raise MathDomainError(node_line, node_char, value)
                elif function_name == 'CH':
                    # Fonction qui renvoie le cosinus hyperbollique
                    result = float_to_bin(math.cosh(value))
                elif function_name == 'SH':
                    # Fonction qui renvoie le sinus hyperbollique
                    result = float_to_bin(math.sinh(value))
                elif function_name == 'TH':
                    # Fonction qui renvoie la tangente hyperbollique
                    result = float_to_bin(math.tanh(value))
                elif function_name == 'CEIL':
                    # Fonction qui renvoie la partie entière supérieure
                    result = float_to_bin(math.ceil(value))
                elif function_name == 'FLOOR':
                    # Fonction qui renvoie la partie entière inférieure
                    result = float_to_bin(math.floor(value))
                elif function_name == 'ROUND':
                    # Fonction qui renvoie l'arrondi
                    result = float_to_bin(round(value))
            elif function_name == 'IABS':
                # Fonction qui renvoie la valeur absolue d'un flottant
                value = bin_to_int(binary_parameters[0])
                result = int_to_bin(abs(value))
            elif function_name == 'POW':
                # Fonction qui renvoie la puissance
                value = bin_to_float(binary_parameters[0])
                power = bin_to_float(binary_parameters[1])
                result = float_to_bin(math.pow(value, power))
            elif function_name == 'MALLOC':
                # Fonction qui effectue une allocation mémoire
                # On récupère la taille qu'on souhaite allouer, puis on fait l'allocation
                size = bin_to_int(binary_parameters[0])
                address = self._malloc(size, line=node_line, char=node_char)

                # On initialise les cases s'il y a plus d'un paramètre dans la fonction
                # Chaque initialisation est une opération élémentaire
                for i, binary_parameter in enumerate(binary_parameters[1:]):
                    self._set_memory(address + i, binary_parameter, line=node_line, char=node_char)
                    yield True, None, node_line, node_char

                result = pointer_to_bin(address)
            elif function_name == 'MALLOC_STRUCT':
                # On regarde la structure qu'on souhaite créer
                struct_name = binary_parameters[0]

                if struct_name not in self.structures_fields:
                    raise UndeclaredStructureError(node_line, node_char, struct_name)

                # On regarde la taille de la structure
                size = len(self.structures_fields[struct_name])
                # On effectue l'allocation
                address = self._malloc(size)
                result = pointer_to_bin(address)
            elif function_name == 'FREE':
                # On récupère le pointeur à libérer
                pointer = bin_to_pointer(binary_parameters[0], line=node_line, char=node_char)
                self._free(pointer)
            elif function_name in ['PRINT', 'PRINTERR']:
                # Fonction d'affichage
                # PRINT(ERR) prend en paramètre des valeurs ou des types
                # Un type qui précède une valeur binaire fait uq'on interprète cette valeur comme ce type avant de l'afficher
                # par exemple PRINT(INT, x, FLOAT, y) interprète x comme un entier et y comme un flottant
                # Si le type est absent, le type STRING est utilisé par défaut.
                # On peut donc par exemple écrire PRINT(INT, x, "\n")

                # On regarde si on veut la sortie ou l'erreur standard
                file = sys.stdout if function_name == 'PRINT' else sys.stderr

                # Enregistre le type qu'on devra utiliser pour afficher la prochaine valeur
                type = None

                for parameter in binary_parameters:
                    # On vérifie si le paramètre est un type
                    parameter_is_type = parameter in ['INT', 'FLOAT', 'BOOL', 'POINTER', 'STRING', 'CHAR']

                    # On ne peut pas mettre deux types à la suite dans PRINT
                    if type is not None and parameter_is_type:
                        raise InvalidTypeParameterInFunctionError(node_line, node_char, function_name, type)
                    # Si c'est un type, on remplace le type en cours
                    if parameter_is_type:
                        type = parameter
                        continue

                    # Sinon c'est une valeur, on l'interprète selon le type en cours
                    if type is None or type == 'STRING':
                        value = self._get_string_from_address(
                            bin_to_pointer(parameter, line=node_line, char=node_char), line=node_line, char=node_char)
                    elif type == 'INT':
                        value = bin_to_int(parameter)
                    elif type == 'FLOAT':
                        value = bin_to_float(parameter)
                    elif type == 'CHAR':
                        value = bin_to_char(parameter, line=node_line, char=node_char)
                    elif type == 'BOOL':
                        value = bin_to_bool(parameter, line=node_line, char=node_char)
                    elif type == 'POINTER':
                        value = bin_to_pointer(parameter, line=node_line, char=node_char)
                    else:
                        # Ce cas ne devrait jamais se produire
                        raise ExecutionError(node_line, node_char, "Unknown error CODE 5, contact developer")

                    # On a interprété une valeur, on peut effacer le type en cours
                    type = None

                    # On affiche la valeur en sortie ou erreur standard
                    print(value, file=file, end='')
            elif function_name in ['FLUSH', 'FLUSHERR']:
                # Fonction de flush
                # FLUSH et FLUSHERR flushent les sorties et erreurs standard

                # On regarde si on veut la sortie ou l'erreur standard
                file = sys.stdout if function_name == 'FLUSH' else sys.stderr
                file.flush()
            elif function_name == 'READ':
                # Fonction 'READ' qui lit 32 bits en entrée standard
                bin = ''

                while True:
                    # On vérifie s'il reste des choses dans le buffer
                    while len(self.input_buffer) > 0:
                        c = self.input_buffer.pop(0)
                        # On ne garde que les caractères 0 et 1, on ignore tout le reste
                        if c in '01':
                            bin += c
                    # Si le mot ne fait pas encore 32 bits, on demande un nouvel input en entrée standard
                    if len(bin) < MAX_NB_BITS:
                        self.input_buffer += list(input())
                        continue
                    break
                # On enregistre le résultat (comme un entier codé avec le binaire bin)
                result = int(bin, 2)
            elif function_name == 'RAND':
                # Fonction qui renvoie un nombre aléatoire entre 0 et 1
                result = float_to_bin(self.random.random())
            elif function_name == 'SRAND':
                # Fonction qui modifie la graîne aléatoire
                value = bin_to_int(binary_parameters[0])
                self.random.seed(value)
            elif function_name == 'I2F':
                # Fonction de cast entier vers flottant
                value = bin_to_int(binary_parameters[0])
                result = float_to_bin(float(value))
            elif function_name == 'F2I':
                # Fonction de cast flottant vers entier
                value = bin_to_float(binary_parameters[0])
                try:
                    x = int(value)
                except OverflowError:
                    raise FloatToIntValueError(node_line, node_char, value)
                if -2 ** (INT_NB_BITS - 1) <= x < 2 ** (INT_NB_BITS - 1):
                    result = int_to_bin(x)
                else:
                    raise FloatToIntValueError(node_line, node_char, value)
            elif function_name == 'I2S':
                # Fonction de cast entier vers string
                # On récupère la valeur à transformer en chaîne, le pointeur où mettre la chaîne et la taille
                # max de la chaîne
                value = bin_to_int(binary_parameters[0])
                address = bin_to_pointer(binary_parameters[1], line=node_line, char=node_char)
                size = bin_to_int(binary_parameters[2])
                # On coupe la chaîne après size caractères
                s = str(value)[:size]
                self._set_string_to_address(s, address, line=node_line, char=node_char)
            elif function_name == 'F2S':
                # Fonction de cast flottant vers string
                # On récupère la valeur à transformer en chaîne, le pointeur où mettre la chaîne et la taille
                # max de la chaîne
                value = bin_to_float(binary_parameters[0])
                address = bin_to_pointer(binary_parameters[1], line=node_line, char=node_char)
                size = bin_to_int(binary_parameters[2])
                # On coupe la chaîne après size caractères
                s = str(value)[:size]
                self._set_string_to_address(s, address, line=node_line, char=node_char)
            elif function_name == 'S2I':
                # Fonction de cast string vers entier
                value = self._get_string_from_address(
                    bin_to_pointer(binary_parameters[0], line=node_line, char=node_char), line=node_line, char=node_char)
                try:
                    # On vérifie que la chaine encode un entier qui est dans la plage
                    x = int(value)
                    if -2**(INT_NB_BITS - 1) <= x < 2**(INT_NB_BITS - 1):
                        result = int_to_bin(x)
                    else:
                        raise StringToIntValueError(node_line, node_char, value)
                except ValueError:
                    raise StringToIntValueError(node_line, node_char, value)
            elif function_name == 'S2F':
                # Fonction de cast string vers flottant
                value = self._get_string_from_address(
                    bin_to_pointer(binary_parameters[0], line=node_line, char=node_char), line=node_line, char=node_char)
                try:
                    result = float_to_bin(float(value))
                except ValueError:
                    raise StringToFloatValueError(node_line, node_char, value)
            elif function_name == 'V2B':
                # Fonction de cast variable vers booléen
                result = bool_to_bin(binary_parameters[0] != 0)
            elif function_name == 'ELEMENTARY_OPERATIONS':
                # Fonction qui renvoie le nombre d'opérations élémentaires exécutées depuis le début du programme
                parameter = binary_parameters[0]
                if parameter == 'INT':
                    result = int_to_bin(self.nb_elementary_operations, overflow=True)
                elif parameter == 'FLOAT':
                    result = float_to_bin(float(self.nb_elementary_operations))
                else:
                    # Ce cas ne devrait jamais se produire
                    raise ExecutionError(node_line, node_line, "Unknown error CODE 6, contact developer")
            else:
                # Fonction custom
                for elementary, value, subnode_line, subnode_char in self.execute_function(function_name, *binary_parameters):
                    # On transfert si l'opération mais pas la valeur
                    yield elementary, None, subnode_line, subnode_char

                    if value is not None:
                        result = value

            # On effectue un yield indiquant qu'on a fait une opération élémentaire, avec sa valeur de retour
            yield True, result, node_line, node_char

        def _execute_arraycall():
            """
            Execute un appel en lecture à un tableau t[i]

            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer T puis i.

            Puis effectue un yield indiquant que
            - que c'est une opération élémentaire
            - qu'il y a une valeur de retour égale au résultat de l'opération
            """

            array = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.arraycall]['array']]
            binary_array = None
            # On calcule la valeur du pointeur correspondant au tableau
            for elementary, value, subnode_line, subnode_char in self.execute_node(array):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_array = value

            index = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.arraycall]['index']]
            binary_index = None
            # On calcule la valeur correspondant à l'indice
            for elementary, value, subnode_line, subnode_char in self.execute_node(index):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_index = value

            address = bin_to_pointer(binary_array, line=node_line, char=node_char)
            index_value = bin_to_int(binary_index)

            result = self._get_memory(address + index_value, line=node_line, char=node_char)

            # On effectue un yield indiquant qu'on a fait une opération élémentaire, avec sa valeur de retour
            yield True, result, node_line, node_char

        def _execute_structcall():
            """
            Exécute un appel en lecture à une structure x->y

            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer x.

            y n'a pas besoin d'être calculé, c'est un identifiant.

            Puis effectue un yield indiquant que
            - que c'est une opération élémentaire
            - qu'il y a une valeur de retour égale au résultat de l'opération
            """
            struct = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.structcall]['struct']]
            binary_struct = None
            # On calcule la valeur du pointeur correspondant au struct
            for elementary, value, subnode_line, subnode_char in self.execute_node(struct):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_struct = value

            # On récupère le champs
            field = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.structcall]['field']][1]

            address = bin_to_pointer(binary_struct, line=node_line, char=node_char)

            # On récupère l'indice du champs dans la structure correspondante.
            try:
                field_index = self.structures_fields_indexes[field]
            except KeyError:
                raise UndeclaredFieldError(node_line, node_char, field)

            result = self._get_memory(address + field_index, line=node_line, char=node_char)

            # On effectue un yield indiquant qu'on a fait une opération élémentaire, avec sa valeur de retour
            yield True, result, node_line, node_char

        def _execute_ifexpr():
            """
            Exécute une condition IF(b1) block1 ELIF(b2) block2... ELSE block3 END

            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer b1, exécute block1 si c'est
            vrai. Sinon teste b2 puis exécute block2...
            Si aucune expression n'est vraie, exécute block3
            """

            token_index = SYNC_AST_CHILDREN_INDEXES[SynCParser.ifexpr]['first_if_token']
            condition_index = SYNC_AST_CHILDREN_INDEXES[SynCParser.ifexpr]['condition_expr']
            block_index = SYNC_AST_CHILDREN_INDEXES[SynCParser.ifexpr]['block']
            while token_index < len(node):
                block = None
                if node[token_index][1] in ['IF', 'ELIF']:
                    condition = node[condition_index]
                    binary_condition = None
                    # On calcule la valeur correspondant au booléen de la condition
                    for elementary, value, subnode_line, subnode_char in self.execute_node(condition):
                        # On transfert si l'opération mais pas la valeur
                        yield elementary, None, subnode_line, subnode_char

                        # Si value est non vide, alors on a une valeur binaire
                        if value is not None:
                            binary_condition = value

                    # On envoie une opération élémentaire disant qu'on a évalué une condition
                    yield True, None, node_line, node_char

                    condition = bin_to_bool(binary_condition, line=node_line, char=node_char)

                    # On vérifie la condition pour savoir quel block on exécuté
                    if condition:
                        block = node[block_index]

                elif node[token_index][1] in ['ELSE']:
                    block = node[token_index + 1]

                if block is not None:
                    for elementary, value, subnode_line, subnode_char in self.execute_node(block):
                        yield elementary, value, subnode_line, subnode_char
                    return
                else:
                    token_index += SYNC_AST_CHILDREN_INDEXES[SynCParser.ifexpr]['if_elif_delta']
                    block_index += SYNC_AST_CHILDREN_INDEXES[SynCParser.ifexpr]['if_elif_delta']
                    condition_index += SYNC_AST_CHILDREN_INDEXES[SynCParser.ifexpr]['if_elif_delta']

        def _execute_forexpr():
            """
            Exécute une boucle for FOR(i;a;b) block ENDFOR

            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer a puis b puis exécute le
            block b - a fois et transfert toutes les opérations élémentaires ou non de ce block.
            """
            variable = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.forexpr]['loop_variable']][1]
            # Si la variable n'a pas été déclarée
            if variable not in self.global_variables and variable not in self.local_variables[-1]:
                self.local_variables[-1].append(variable)

            address = self._get_variable_address(variable, line=node_line, char=node_char)
            # La déclaration d'une variable n'est pas une opération élémentaire. On ne fait pas de yield.

            start_expr = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.forexpr]['start_expr']]
            binary_start_expr = None
            # On calcule la valeur correspondant à l'indice de début de la boucle FOR
            for elementary, value, subnode_line, subnode_char in self.execute_node(start_expr):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_start_expr = value

            start_expr = bin_to_int(binary_start_expr)

            end_expr = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.forexpr]['end_expr']]
            binary_end_expr = None
            # On calcule la valeur correspondant à l'indice de fin de la boucle FOR
            for elementary, value, subnode_line, subnode_char in self.execute_node(end_expr):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_end_expr = value
            end_expr = bin_to_int(binary_end_expr)

            block = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.forexpr]['block']]

            self._set_memory(address, int_to_bin(start_expr), line=node_line, char=node_char)

            # On indique qu'on fait une opération élémentaire consistant à affecter la valeur start_expr à l'adresse
            # indiquée
            yield True, None, node_line, node_char

            # On indique qu'on fait une opération élémentaire consistant tester la condition d'arrêt
            yield True, None, node_line, node_char

            while bin_to_int(self._get_memory(address, line=node_line, char=node_char)) < end_expr:

                # On éxécute le block et on transfert les opérations
                for elementary, value, subnode_line, subnode_char in self.execute_node(block):
                    if value == 'CONTINUE':
                        yield elementary, None, subnode_line, subnode_char
                        # On casse la boucle for pour cesser toute exécution du block et on continue la boucle for
                        break
                    elif value == 'BREAK':
                        yield elementary, None, subnode_line, subnode_char
                        # On cesse l'exécution de cette boucle
                        return
                    yield elementary, value, subnode_line, subnode_char

                self._set_memory(address, int_to_bin(bin_to_int(self._get_memory(address, line=node_line, char=node_char)) + 1),
                                 line=node_line, char=node_char)
                # On indique qu'on fait deux opérations élémentaires consistant à incrémenter la valeur indiquée à
                # l'adresse
                yield True, None, node_line, node_char
                yield True, None, node_line, node_char

                # On indique qu'on fait une opération élémentaire consistant tester la condition d'arrêt
                yield True, None, node_line, node_char

        def _execute_whileexpr():
            """
            Exécute une boucle while WHILE(b) block ENDWHILE

            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer b puis si b est faux,
            exécute le block. Recommence tant que b est faux.
            """
            condition_node = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.whileexpr]['condition_expr']]
            block = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.whileexpr]['block']]

            while True:
                binary_condition = None
                # On calcule la valeur correspondant au booléen de la condition
                for elementary, value, subnode_line, subnode_char in self.execute_node(condition_node):
                    if elementary:
                        # On indique au noeud supérieur qu'une opération élémentaire a eu lieu,
                        # mais il n'y a pas de valeur de retour
                        yield True, None, subnode_line, subnode_char

                    # Si value est non vide, alors on a une valeur binaire
                    if value is not None:
                        binary_condition = value

                condition = bin_to_bool(binary_condition, line=node_line, char=node_char)

                # On envoie une opération élémentaire disant qu'on a évalué une condition
                yield True, None, node_line, node_char

                # On vérifie la condition pour savoir si on exécute le block ou non
                if condition:
                    # On exécute le block et on transfert toutes les opérations et valeurs
                    for elementary, value, subnode_line, subnode_char in self.execute_node(block):
                        if value == 'CONTINUE':
                            yield elementary, None, subnode_line, subnode_char
                            # On casse la boucle for pour cesser toute exécution du block et on continue la boucle while
                            break
                        elif value == 'BREAK':
                            yield elementary, None, subnode_line, subnode_char
                            # On cesse l'exécution de cette boucle
                            return
                        yield elementary, value, subnode_line, subnode_char
                else:
                    break

        def _execute_continuerule():
            """
            Yield une opération non élémentaire indiquant qu'on a excuté la commande CONTINUE. Si cette opération est
            transférée à une boucle FOR ou WHILE, passe à l'itération suivante.
            """
            yield False, 'CONTINUE', node_line, node_char

        def _execute_breakrule():
            """
            Yield une opération non élémentaire indiquant qu'on a excuté la commande CONTINUE. Si cette opération est
            transférée à une boucle FOR ou WHILE, coupe la boucle.
            """
            yield False, 'BREAK', node_line, node_char

        def _execute_returnrule():
            """
            Exécute un return RETURN x

            Effectue un yield pour chaque opération élémentaire nécessaire pour calculer x.

            Puis effectue un yield indiquant que
            - que c'est une opération élémentaire
            - qu'il y a une valeur de retour égale au tuple (RETURN, valeur de x)

            Si ce tuple est transféré à une fonction en cours d'exécution, termine la fonction.
            """

            expr = node[SYNC_AST_CHILDREN_INDEXES[SynCParser.returnrule]['expr']]
            binary_value = None
            # On calcule la valeur correspondant au membre de droite
            for elementary, value, subnode_line, subnode_char in self.execute_node(expr):
                # On transfert si l'opération mais pas la valeur
                yield elementary, None, subnode_line, subnode_char

                # Si value est non vide, alors on a une valeur binaire
                if value is not None:
                    binary_value = value

            # Return n'est pas une opération élémentaire mais renvoie une valeur
            # Sinon un appel de fonction custom comptera pour deux opérations élémentaires s'il ya un return
            # On précise qu'il s'agit d'un return
            yield False, ('RETURN', binary_value), node_line, node_char

        def _execute_block():
            """
            Execute les instructions d'un block

            Effectue un yield pour chaque opération élémentaire ou non nécessaire pour calculer toutes les commandes
            de ce block.
            """
            start, end, step = SYNC_AST_CHILDREN_INDEXES[SynCParser.block]['blockexprs']
            for blockexpr in node[start:end:step]:
                for elementary, value, node_line, node_char in self.execute_node(blockexpr):
                    yield elementary, value, node_line, node_char

        # Dictionnaire qui à chaque type de noeud associe la fonction à exécuter
        type_to_function = {
            SynCParser.atom: _execute_atom,
            SynCParser.affect: _execute_affect,
            SynCParser.arrayaffect: _execute_arrayaffect,
            SynCParser.structaffect: _execute_structaffect,
            SynCParser.derefaffect: _execute_derefaffect,
            SynCParser.bracketexpr: _execute_bracketexpr,
            SynCParser.multdivexpr: _execute_binaryoperator,
            SynCParser.addsubexpr: _execute_binaryoperator,
            SynCParser.moduloexpr: _execute_binaryoperator,
            SynCParser.cmpexpr: _execute_binaryoperator,
            SynCParser.eqexpr: _execute_binaryoperator,
            SynCParser.boolexpr: _execute_boolbinaryoperator,  # N'est pas fait pareil à cause des shortcut
            SynCParser.notexpr: _execute_unaryoperator,
            SynCParser.derefexpr: _execute_unaryoperator,
            SynCParser.refexpr: _execute_refexpr,
            SynCParser.call: _execute_call,
            SynCParser.arraycall: _execute_arraycall,
            SynCParser.structcall: _execute_structcall,
            SynCParser.ifexpr: _execute_ifexpr,
            SynCParser.forexpr: _execute_forexpr,
            SynCParser.whileexpr: _execute_whileexpr,
            SynCParser.continuerule: _execute_continuerule,
            SynCParser.breakrule: _execute_breakrule,
            SynCParser.returnrule: _execute_returnrule,
            SynCParser.block: _execute_block,
        }

        # On exécute la fonction
        for elementary, value, node_line, node_char in type_to_function[node[0]]():
            # On transfert le résultat des opérations élémentaires ou non
            # On ne filtre pas les opérations non élémentaires, sinon, certaines valeurs ne passeront pas,
            # comme les valeurs atomiques dont le calcul n'est pas élémentaire.
            yield elementary, value, node_line, node_char


def _get_program(program_filename=None, input_program=None):
    """
    :param program_filename: chemin vers un fichier contenant un programme SynC
    :param input_program: une chaîne de caractère contenant un programme SynC, ignoré si program_filename est donné
    :return: le programme correspondant au fichier ou à la chaîne donné(e) en entrée.
    """
    if program_filename is not None:
        with open(program_filename, 'r') as f:
            input_program = ''.join(f.readlines())

    SynCParser.pre_compile_grammar(pre_compiled=PRECOMPILED_GRAMMAR)
    tree = SynCParser.parse(input_program)
    program = SynCProgram(tree)

    return program


def get_program_execution_iterator(program_filename=None, input_program=None):
    """
    :param program_filename: chemin vers un fichier contenant un programme SynC
    :param input_program: une chaîne de caractère contenant un programme SynC, ignoré si program_filename est donné
    :return un itérateur sur les opérations élémentaires du programme program_file.
    """

    program = _get_program(program_filename=program_filename, input_program=input_program)
    return program.main_function_iterator()


def execute_program(program_filename=None, input_program=None):
    """
    Exécute le programme en entrée
    :param program_filename: chemin vers un fichier contenant un programme SynC
    :param input_program: une chaîne de caractère contenant un programme SynC, ignoré si program_filename est donné
    """
    for _ in get_program_execution_iterator(program_filename=program_filename, input_program=input_program):
        pass


def check_program(program_filename=None, input_program=None):
    """
    Teste le programme en entrée. Vérifie que la syntaxe est conforme à la grammaire et que le programme ne renvoie
    aucune erreur autre que les erreurs d'exécutions (absence de fonction main, deux structures avec le même nom, ...)
    Une exception est leée si le programme a provoqué une erreur. Sinon rien ne se passe.
    :param program_filename: chemin vers un fichier contenant un programme SynC
    :param input_program: une chaîne de caractère contenant un programme SynC, ignoré si program_filename est donné
    """

    try:
        _get_program(program_filename=program_filename, input_program=input_program)
    except Exception as e:
        raise e
