"""
Fichier contenant des fonctions de conversions entre des valeurs binaires SYNC et des valeurs typées (entier, flottant,
booléen, pointeur, caractère)

Contient également quelques constantes utiles sur la mémoire d'un programme SYNC
"""

import struct
from src.sync.execution_exceptions import *


MAX_NB_BITS = 32
INT_NB_BITS = MAX_NB_BITS
FLOAT_NB_BITS = MAX_NB_BITS
POINTER_NB_BITS = 24
CHAR_NB_BITS = 7

NULL_ADDRESS = 0
FALSE_ENCODING = 0
TRUE_ENCODING = 1

MEMORY_SIZE = 2**POINTER_NB_BITS

# Mot clef utilisé pour les valeurs non typées
# Il n'y a pas de tel litéral dans la grammaire
# Un binaire non typé est juste une valeur sur 32bits qui n'est pas interprétée comme un type ou un autre.
# Cette valeur est écrite en python sous forme d'un entier entre 0 et 2**32 - 1.
# Lors de l'exécution d'un programme, on va successivement effectuer les opérations du programme. Par exemple, toute
# valeur litérel typée sera remplacée par sa valeur binaire associée. Par exemple dans x = -1, on remplace le -1 par
# le binaire 111111...1111.
# Autre exemple, lors de l'évaluation d'une variable, on la remplace par sa valeur binaire.
# Pour savoir que ce binaire est un binaire et pas l'entier 2**32 - 1, le mot clef assicié à cette valeur est
# BINARY_KEYWORD.
BINARY_KEYWORD = "SYNC_Binary"


def bin_to_int(x):
    """
    Les mots binaires de la mémoire des programmes sont codés avec 32 bits, ils sont stockés dans la mémoire de cet
    interpréteur comme des entiers positifs pythons codés sur 32 bits, plutôt que comme des chaînes de caractère.
    Les entiers en SYNC sont codés en complément à 2.

    Les entiers en python sont codés différemment. On utilise donc le programme ci-dessous pour transformer l'entier x
    en calculant sa valeur codée en binaire en python, puis en calculant l'entier correspondant en complément à 2.
    L'entier pyton étant positif, il s'agit juste de l'entier entre 0 et 2**32 - 1 correspondant au codage binaire sur
    32 bits.

    Cela se fait assez simplement :
    si x < 2**31 alors on renvoie x
    sinon on renvoie x - 2**32
    """
    if x < 2**(INT_NB_BITS - 1):
        return x
    else:
        return x - 2**INT_NB_BITS


def int_to_bin(x, overflow=False):
    """
    Fontion inverse de bin_to_int
    On suppose que l'entier appartient à la bonne plage.

    Si overflow est Vrai, commence par mettre x entre -2**31 et 2**31 - 1
    """

    if overflow:
        while x >= 2**(INT_NB_BITS - 1):
            x -= 2**INT_NB_BITS
        while x < -2**INT_NB_BITS:
            x += 2**INT_NB_BITS

    if x < 0:
        return x + 2**INT_NB_BITS
    else:
        return x


def float_to_bin(x):
    """
    Encode x en IEEE-754 en 32 bits puis renvoie l'entier python positif codé avec les mêmes bits.
    """
    try:
        return int('{:d}'.format(struct.unpack('>I', struct.pack('!f', x))[0]))
    except OverflowError:
        # f est trop grand (positivement ou négativement)
        # On renvoie l'infini si f est positif et -l'infini sinon
        if x > 0:
            return 2139095040
        else:
            return 4286578688


def bin_to_float(x):
    """
    Encore l'entier x en binaire puis renvoie le flottant codé en 32 bit avec IEEE-754
    """
    return struct.unpack('!f', x.to_bytes(4, byteorder='big'))[0]


def char_to_bin(x):
    """
    Encode le caractère en entier python codé sur 8 bit, cela revient à appeler ord.
    """
    try:
        return ord(x)
    except TypeError:
        if x == '\\n':
            x = '\n'
        elif x == '\\0':
            x = '\0'
        elif x == '\\v':
            x = '\v'
        elif x == '\\f':
            x = '\f'
        elif x == '\\r':
            x = '\r'
        elif x == '\\t':
            x = '\t'
        return ord(x)


def bin_to_char(x, line=None, char=None):
    """
    Encode l'entier x en binaire puis renvoie le charactère correspondant.
    Cela revient juste à appeler la fonction chr.
    Si l'entier x est supérieur à 128, renvoie une exception.

    line et char indiquent des informations de la ligne et le caractère du programme où on a eu
     besoin d'accéder à cette adresse et servent en cas d'exception.
    """
    if x <= 2**CHAR_NB_BITS:
        return chr(x)
    else:
        raise WrongCharacterCodeError(line, char, x)


def bool_to_bin(x):
    """
    Vrai est codé avec 1 et faux avec 0. Renvoie l'entier codant le booléen x.
    """
    return 1 if x else 0


def bin_to_bool(x, line=None, char=None):
    """
    Vrai est codé avec 1 et faux avec 0. Renvoie le booléen codé avec x.
    Si x n'est ni 1 ni 0, renvoie une exception.

    line et char indiquent des informations de la ligne et le caractère du programme où on a eu
     besoin d'accéder à cette adresse et servent en cas d'exception.
    """
    if x == 1:
        return True
    elif x == 0:
        return False
    else:
        raise WrongBooleanCodeError(line, char, x)


def bin_to_pointer(x, line=None, char=None):
    """
    Un pointeur est juste un entier représentant l'adresse pointée, cette fonction est donc exactement la même que
    bin_to_int à l'exception près que les adresses des pointeurs ne vont que jusqu'à 2**24 - 1.

    Dans le cas contraire, une exception est levée.

    line et char indiquent des informations de la ligne et le caractère du programme où on a eu
     besoin d'accéder à cette adresse et servent en cas d'exception.
    """
    if x < MEMORY_SIZE:
        return bin_to_int(x)
    else:
        raise WrongPointerCodeError(line, char, x)


def pointer_to_bin(x):
    """
    Fontion inverse de bin_to_pointer.
    On suppose que le pointeur appartient à la bonne plage
    """
    return int_to_bin(x)


def literal_to_bin(x):
    """
    Renvoie les codes binaires des valeurs constantes NULL, FALSE et TRUE
    """
    if x == 'NULL':
        return NULL_ADDRESS
    elif x == 'FALSE':
        return FALSE_ENCODING
    elif x == 'TRUE':
        return TRUE_ENCODING


def bin_to_string(x):
    """
    :param x: entier entre 0 et 2**MAX_NB_BITS - 1
    :return: La chaîne de caractère binaire qui encode x, avec 32 bits (et des 0 devant si nécessaire)
    """
    form = '{:0%db}' % MAX_NB_BITS
    return form.format(x)