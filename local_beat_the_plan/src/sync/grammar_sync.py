"""
Grammaire du langage SYN-C
"""

import lrparsing
from lrparsing import List, Prio, Ref, Token, Tokens, Repeat, Opt, Many


class SynCParser(lrparsing.Grammar):
    class T(lrparsing.TokenRegistry):
        """Token principaux du langage :
        entiers, flottants, identifiants, caractères, chaînes de caractères et fonction prédéfinies"""
        integer = Token(re="-?[0-9]+")
        floatn = Token(re="-?([0-9]+\.[0-9]+)(e-?[0-9]+)?")
        ident = Token(re="[a-z][A-Za-z_0-9]*")
        char = Token(re="'(\\\\)?[ -~]'")
        string = Token(re='"[^"]*"')  # TODO : régler le problème du caractère \"

        libfunctions = Tokens('IABS FABS COS SIN TAN SQRT EXP LN POW SH CH TH CEIL FLOOR ROUND MALLOC MALLOC_STRUCT FREE '
                              'READ RAND SRAND I2F I2S F2I F2S S2I S2F V2B FLUSH FLUSHERR')

    # Expressions avec opérateurs ou appel de fonction
    _expr = Ref("_expr")

    # Appel de fonction
    call = ((T.ident | T.libfunctions) + '(' + List(_expr, ',') + ')') | \
        (Tokens('PRINT PRINTERR') + '(' + List((_expr | Tokens('INT FLOAT BOOL POINTER STRING CHAR')), ',') + ')') | \
        (Tokens('ELEMENTARY_OPERATIONS') + '(' + Tokens('INT FLOAT') + ')')

    # Appel à un tableau
    arraycall = _expr + '[' + _expr + ']'

    # Appel d'un champs d'une structure
    structcall = _expr << '->' << T.ident

    # Littéraux atomiques
    atom = T.ident | \
            T.integer | \
            T.floatn | \
            T.char | \
            T.string | \
            Tokens('TRUE FALSE NULL')

    # Expression parenthésée (utilisée pour les priorités dans les expressions)
    bracketexpr = Token('(') + _expr + ')'

    # Non logique
    notexpr = Tokens("NOT") >> _expr

    # Déréférencement
    derefexpr = '$' >> _expr

    # Référencement
    refexpr = Tokens("&") >> T.ident

    # Produit et division
    multdivexpr = _expr << Tokens("* / *. /.") << _expr

    # Modulo
    moduloexpr = _expr << Tokens("%") << _expr

    # Addition et soustraction
    addsubexpr = _expr << Tokens("+ - +. -.") << _expr

    # Comparaisons
    cmpexpr = _expr << Tokens("<= >= < > >=. <=. <. >.") << _expr

    # Egalité
    eqexpr = _expr << Tokens("== !=") << _expr

    # Et et Ou logiques
    boolexpr = _expr << Tokens("AND OR") << _expr

    # Ensemble des expressions avec opérateurs par priorité
    _expr = Prio(
            call,
            arraycall,
            structcall,
            atom,
            bracketexpr,
            notexpr,
            derefexpr,
            refexpr,
            multdivexpr,
            moduloexpr,
            addsubexpr,
            cmpexpr,
            eqexpr,
            boolexpr
    )

    # Types de lignes dans un bloc, notamment dans les fonctions

    # Condition
    ifexpr = Ref("ifexpr")

    # Boucle For
    forexpr = Ref("forexpr")

    # Boucle while
    whileexpr = Ref("whileexpr")

    # Affectation
    # Pour les 3 dernier, on n'utilise pas les mots clefs arraycall, structcall et derefexpr
    # pour simplifier l'interprétation des programmes.
    # Un arraycall, structcall ou derefexpr est interprété comme une opération donnant une valeur
    # alors que le membre gauche d'un arrayaffect, structaffect, derefaffect est interprété comme une variable
    # devant recevoir une valeur.
    affect = T.ident + '=' + _expr
    arrayaffect = _expr + '[' + _expr + ']' + '=' + _expr
    structaffect = (_expr << '->' << T.ident) + '=' + _expr
    derefaffect = ('$' >> _expr) + '=' + _expr

    _affect = Prio(arrayaffect | structaffect | derefaffect | affect)

     # Return
    returnrule = Token('RETURN') + _expr

    # Continue
    continuerule = Token('CONTINUE')

    # Continue
    breakrule = Token('BREAK')

    # Ensemble des expressions pouvant apparaître comme une commande dans un block, à l'exception
    _blockexpr = _affect | returnrule | ifexpr | whileexpr | forexpr | call | continuerule | breakrule

    block = Repeat(_blockexpr)

    # Conditions et boucles
    ifexpr = (Token('IF') + '(' + _expr + ')' + block + Many(Token('ELIF') + '(' + _expr + ')' + block)
              + Opt(Token('ELSE') + block) + Token('ENDIF'))
    forexpr = Token('FOR') + '(' + T.ident + ';' + _expr + ';' + _expr + ')' + block + Token('ENDFOR')
    whileexpr = Token('WHILE') + '(' + _expr + ')' + block + Token('ENDWHILE')

    # Variables globales
    globalaffect = T.ident + '=' + (T.integer | T.floatn | T.char | T.string | Tokens('TRUE FALSE NULL'))
    globalsdecl = Token('GLOBALS') + Repeat(globalaffect) + Token('ENDGLOBALS')

    # Déclaration des STRUCT et FONCTIONS
    structdecl = Token('STRUCT') + Repeat(T.ident, min=2) + Token('ENDSTRUCT')
    fundecl = Token('FUNCTION') + T.ident + '(' + List(T.ident, ',') + ')' + block + Token('END')

    # Programme
    prog = Opt(globalsdecl) + Repeat(structdecl) + Repeat(fundecl, min=1)
    START = prog
    COMMENTS = (
        Token(re="//(?:[^\r\n]*)$") |
        Token(re="/[*](?:[^*]|[*][^/])*[*]/"))


def get_line_of_node(node):
    if node[0] == SynCParser.block:
        return None
    try:
        line_indexes = SYNC_AST_CHILDREN_INDEXES[node[0]]['line']
    except KeyError:
        line_indexes = [-2]
    for index in line_indexes:
        node = node[index]
    return node


def get_char_of_node(node):
    if node[0] == SynCParser.block:
        return None
    try:
        char_indexes = SYNC_AST_CHILDREN_INDEXES[node[0]]['char']
    except KeyError:
        char_indexes = [-1]
    for index in char_indexes:
        node = node[index]
    return node


"""
Indique, pour chaque type de noeud, les indices de ses enfants utiles dans l'arbre syntaxique abstrait. Ces 
indices sont dans un dictionnaire. Le nom est juste un mot-clef qui peut être utilisé. 
La valeur est soit un entier, correspondant à un indice entier, soit un tableau dans le cas d'un REPEAT ou d'une LIST.
Le tableau correspond à un range (start, end, step), le dernier indice est end - 1. 

Deux cas particulier : line et char qui permettent de trouver la ligne et la colonne associé à ce noeud dans le rpogramme
Par exemple pour une affectation, il s'agit de la ligne et la colonne du symbole '='
Il s'agit alors d'un tableau d'indices successif à utiliser pour tomber sur la ligne ou la colonne. On utilise alors
get_get_line_of_node et get_char_of_node pour trouver ces lignes et caractères.

Le if étant moins statique que les autres mots clef, ses enfants sont définis autrement
"""
SYNC_AST_CHILDREN_INDEXES = {
    SynCParser.atom: {'literal': 1, 'line': [1, -2], 'char': [1, -1]},
    SynCParser.call: {'function_name': 1, 'parameters': [3, -1, 2], 'line': [2, -2], 'char': [2, -1]},
    SynCParser.arraycall: {'array': 1, 'index': 3, 'line': [2, -2], 'char': [2, -1]},
    SynCParser.structcall: {'struct': 1, 'field': 3, 'line': [2, -2], 'char': [2, -1]},
    SynCParser.bracketexpr: {'expr': 2, 'line': [1, -2], 'char': [1, -1]},
    SynCParser.notexpr: {'operator': 1, 'expr': 2, 'line': [1, -2], 'char': [1, -1]},
    SynCParser.derefexpr: {'operator': 1, 'expr': 2, 'line': [1, -2], 'char': [1, -1]},
    SynCParser.refexpr: {'operator': 1, 'variable': 2, 'line': [1, -2], 'char': [1, -1]},
    SynCParser.multdivexpr: {'left_expr': 1, 'operator': 2, 'right_expr': 3, 'line': [2, -2], 'char': [2, -1]},
    SynCParser.moduloexpr: {'left_expr': 1, 'operator': 2, 'right_expr': 3, 'line': [2, -2], 'char': [2, -1]},
    SynCParser.addsubexpr: {'left_expr': 1, 'operator': 2, 'right_expr': 3, 'line': [2, -2], 'char': [2, -1]},
    SynCParser.cmpexpr: {'left_expr': 1, 'operator': 2, 'right_expr': 3, 'line': [2, -2], 'char': [2, -1]},
    SynCParser.eqexpr: {'left_expr': 1, 'operator': 2, 'right_expr': 3, 'line': [2, -2], 'char': [2, -1]},
    SynCParser.boolexpr: {'left_expr': 1, 'operator': 2, 'right_expr': 3, 'line': [2, -2], 'char': [2, -1]},
    SynCParser.affect: {'variable': 1, 'expr': 3, 'line': [2, -2], 'char': [2, -1]},
    SynCParser.arrayaffect: {'array': 1, 'index': 3, 'expr': 6, 'line': [5, -2], 'char': [5, -1]},
    SynCParser.structaffect: {'struct': 1, 'field': 3, 'expr': 5, 'line': [4, -2], 'char': [4, -1]},
    SynCParser.derefaffect: {'pointer': 2, 'expr': 4, 'line': [1, -2], 'char': [1, -1]},
    SynCParser.returnrule: {'expr': 2, 'line': [1, -2], 'char': [1, -1]},
    SynCParser.block: {'blockexprs': [1, None, 1]},
    SynCParser.ifexpr: {'first_if_token': 1, 'condition_expr': 3, 'block': 5, 'if_elif_delta': 5, 'line': [1, -2], 'char': [1, -1]},
    SynCParser.forexpr: {'loop_variable': 3, 'start_expr': 5, 'end_expr': 7, 'block': 9, 'line': [1, -2], 'char': [1, -1]},
    SynCParser.whileexpr: {'condition_expr': 3, 'block': 5, 'line': [1, -2], 'char': [1, -1]},
    SynCParser.globalaffect: {'variable': 1, 'value': 3, 'line': [2, -2], 'char': [2, -1]},
    SynCParser.globalsdecl: {'global_variables': [2, -1, 1], 'line': [1, -2], 'char': [1, -1]},
    SynCParser.structdecl: {'struct_name': 2, 'fields': [3, -1, 1], 'line': [1, -2], 'char': [1, -1]},
    SynCParser.fundecl: {'function_name': 2, 'parameters': [4, -3, 2], 'block': -2, 'line': [1, -2], 'char': [1, -1]},
    SynCParser.breakrule: {'line': [1, -2], 'char': [1, -1]},
    SynCParser.continuerule: {'line': [1, -2], 'char': [1, -1]}
}
