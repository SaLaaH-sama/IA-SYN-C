
class ExecutionError(Exception):
    def __init__(self, line, char, message):
        if line is not None and char is not None:
            super().__init__("Line %s, Char %s : %s" % (line, char, message))
        elif line is not None:
            super().__init__("Line %s : %s" % (line, message))
        elif char is not None:
            super().__init__("Char %s : %s" % (char, message))
        else:
            super().__init__(message)


class SameNameStructureError(ExecutionError):
    """ Envoyée quand deux structures ont le même nom """
    def __init__(self, line, char, structure_name):
        super().__init__(line, char, "Structure %s is declared twice." % structure_name)


class SameFieldsNameStructureError(ExecutionError):
    """ Envoyée quand une structure a deux fois le même champs """
    def __init__(self, line, char, structure_name, field_name):
        super().__init__(line, char, "Structure %s has twice the field %s." % (structure_name, field_name))


class SameFieldStructureError(ExecutionError):
    """ Envoyée quand deux structures ont le même champs """
    def __init__(self, line, char, structure1_name, structure2_name, field_name):
        super().__init__(line, char, "Structures %s and %s have the same field %s." %
                         (structure1_name, structure2_name, field_name))


class SameNameFunctionError(ExecutionError):
    """ Envoyée quand deux fonctions ont le même nom """

    def __init__(self, line, char, function_name):
        super().__init__(line, char, "Function %s is declared twice." % function_name)


class SameParametersNameFunctionError(ExecutionError):
    """ Envoyée quand une fonction a deux paramètres qui ont le même nom """

    def __init__(self, line, char, function_name, parameter_name):
        super().__init__(line, char, "Function %s has twice the parameter %s." %
                         (function_name, parameter_name))


class SameGlobalVariableNameError(ExecutionError):
    """ Envoyée quand deux variables globales ont le même nom """
    def __init__(self, line, char, variable_name):
        super().__init__(line, char, "Global variable %s is declared twice." % variable_name)


class NoMainFunctionError(ExecutionError):
    """ Envoyée quand il n'y a pas de fonction main """

    def __init__(self):
        super().__init__(None, None, "There is no main function in the program.")


class MainFunctionWithParametersError(ExecutionError):
    """ Envoyée quand la fonction main a des paramètres d'entrée. """

    def __init__(self, line, char):
        super().__init__(line, char, "main function should not contain any input parameter.")


class WrongBooleanCodeError(ExecutionError):
    """Envoyé quand le programme essaie d'interpréter un binaire autre que 000..000 ou 000...001 en booléen. """

    def __init__(self, line, char, code):
        super().__init__(line, char, "Cannot code boolean with %s. Boolean should be coded with 0000...000X."
                         % '{0:032b}'.format(code))


class WrongCharacterCodeError(ExecutionError):
    """Envoyé quand le programme essaie d'interpréter un binaire autre que 000..0000XXXXXXX en caractère. """

    def __init__(self, line, char, code):
        super().__init__(line, char, "Cannot code character with %s. Characters should be coded with "
                                     "0000...0000XXXXXXX." % '{0:032b}'.format(code))


class WrongPointerCodeError(ExecutionError):
    """Envoyé quand le programme essaie d'interpréter un binaire autre que 00000000XXXXXXXXXXXXXXXXXXXXXXXX
    en pointeur. """

    def __init__(self, line, char, code):
        super().__init__(line, char, "Cannot code pointer with %s. Pointers should be coded "
                                     "with 000000000XXXXXXXXXXXXXXXXXXXXXXXX." % '{0:032b}'.format(code))


class NonValidCharacterError(ExecutionError):
    """Envoyé quand une chaîne de caractère du programme écrit en dur n'est pas autorisé. """

    def __init__(self, line, char, character):
        super().__init__(line, char, "Program contains non valid character : '%s'." % character)


class NonValidIntegerError(ExecutionError):
    """Envoyé quand un entier écrit dans le programme dépasse la plage autorisée. """

    def __init__(self, line, char, integer):
        super().__init__(line, char, "Program contains non valid integer : %s." % integer)


class InvalidTypeParameterInFunctionError(ExecutionError):
    """Envoyé quand les paramètres des fonctions ne sont pas corrects. """

    def __init__(self, line, char, function_name, parameter):
        super().__init__(line, char, "Wrong parameter %s in function %s." % (parameter, function_name))


class IncorrectNumberOfParametersInFunction(ExecutionError):
    """Envoyé quand le nombre de paramètres des fonctions n'est pas bon. """

    def __init__(self, line, char, function_name):
        super().__init__(line, char, "Wrong number of parameters in function %s." % function_name)


class MallocNegativeSizeError(ExecutionError):
    """Envoyé quand on effectue un malloc avec une taille négative. """

    def __init__(self, line, char):
        super().__init__(line, char, "Malloc cannot be called with negative or nul size.")


class FreeNotAllocatedPointer(ExecutionError):
    """Envoyé quand on effectue un free sur un pointeur qui n'a pas été alloué avec malloc. """

    def __init__(self, line, char):
        super().__init__(line, char, "Free can be called only on pointers allocated with malloc.")


class MemoryAccessError(ExecutionError):
    """Envoyé quand on essaie d'accéder à une case mémoire en dehors de la plage autorisée. """

    def __init__(self, line, char, address):
        super().__init__(line, char, "Memory cannote be accessed at address %d." % address)


class MemoryExceededError(ExecutionError):
    """Envoyé quand il n'y a plus de mémoire disponible. """

    def __init__(self, line, char, variable_name):
        super().__init__(line, char, "Memory limit exceeded while declaring variable %s." % variable_name)


class ReadOnlyMemoryWriteError(ExecutionError):
    """Envoyé quand on essaie de modifier la mémoire à une case mémoire qui est read-only. """

    def __init__(self, line, char, address):
        super().__init__(line, char, "The address %d is read-only." % address)


class UndeclaredVariableError(ExecutionError):
    """Envoyé quand on cherche à accéder à une variable inconnue. """

    def __init__(self, line, char, variable_name):
        super().__init__(line, char, "Variable %s was not declared." % variable_name)


class UndeclaredFunctionError(ExecutionError):
    """Envoyé quand on cherche à accéder à une fonction inconnue. """

    def __init__(self, line, char, function_name):
        super().__init__(line, char, "Function %s was not declared." % function_name)


class UndeclaredStructureError(ExecutionError):
    """Envoyé quand on cherche à créer une variable de type structure inconnue. """

    def __init__(self, line, char, struct_name):
        super().__init__(line, char, "Structure %s was not declared." % struct_name)


class UndeclaredFieldError(ExecutionError):
    """Envoyé quand on cherche à accéder à un champs d'une structure inconnue. """

    def __init__(self, line, char, field_name):
        super().__init__(line, char, "The field %s was not declared in any structure." % field_name)


class StringToIntValueError(ExecutionError):
    """Envoyé quand on cherche à transformer une chaine en entier et que la chaine n'est pas un entier ou est un entier
    qui n'estp as dans la plage. """

    def __init__(self, line, char, s):
        super().__init__(line, char, "String %s cannot be casted to integer." % s)


class FloatToIntValueError(ExecutionError):
    """Envoyé quand on cherche à transformer un float en entier et que le float est un entier
    qui n'est pas dans la plage. """

    def __init__(self, line, char, f):
        super().__init__(line, char, "Float %.2f cannot be casted to integer." % f)


class StringToFloatValueError(ExecutionError):
    """Envoyé quand on cherche à transformer une chaine en flottant et que la chaine n'est pas un flottant. """

    def __init__(self, line, char, s):
        super().__init__(line, char, "String %s cannot be casted to float." % s)


class MathDomainError(ExecutionError):
    """Envoyé quand on cherche à exécuter une fonction ave un paramètre non défini pour cette fonction, par exemple
    log d'un nombre négatif. """

    def __init__(self, line, char, value):
        super().__init__(line, char, "Operation is undefined for value %.2f." % value)


class GlobalVariableAndFunctionParameterWithSameNameError(ExecutionError):
    """Envoyé quand une variable globale et un paramètre d'entrée d'une fonction ont le même nom."""

    def __init__(self, line, char, global_variable_name, function_name):
        super().__init__(line, char, "Global variable %s has the same name as a parameter of function %s." % (global_variable_name, function_name))
