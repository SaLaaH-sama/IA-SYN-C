from abc import ABC, abstractmethod
from functools import cmp_to_key
from collections import defaultdict
import re
import math


def keywords_ordering(s1, s2):
    """
    Comparator ordering the string with the natural ordering except for the strings "translateX" and "translateY"
    which are placed in the first and second places.
    """
    if s1 is None and s2 is None:
        return 0
    if s1 is None:
        return -1
    if s2 is None:
        return 1
    if s1 == s2:
        return 0
    if s1 == "translateX":
        return -1
    if s2 == "translateX":
        return 1
    if s1 == "translateY":
        return -1
    if s2 == "translateY":
        return 1
    return s1 <= s2


def get_keyword_key():
    return cmp_to_key(keywords_ordering)


class Shape(ABC):
    """
    This class represents a SVG shape.
    The class is, obviously, abstract and should be extended to represent a specific SVG shape as a rectangle.
    """

    _last_id = 0

    def __init__(self, name):
        """
        Build a new shape.
        The default shape has a black thin stroke and a white fill color. The opacity is 1.
        The translation, rotation and scales are set to default value (0 for the two first one and 1 for the last one)

        :param name: name of the SVG shape, used to define the id of the SVG tag, with the id attribute.
        """

        # Name of the shape, used to define the id of the SVG tag with the id attribute.
        self._name = name

        # Id of the shape, used to define the id of the SVG tag with the name attribute.
        self._id = Shape._last_id

        # Increment the next id of the shapes
        Shape._last_id += 1

        # Red value of the stroke color, should be integer between 0 and 255
        self._red_stroke_color = 0

        # Green value of the stroke color, should be integer between 0 and 255
        self._green_stroke_color = 0

        # Blue value of the stroke color, should be integer between 0 and 255
        self._blue_stroke_color = 0

        # Stroke opacity of the shape, between 0 and 1. 0 means stroke invisible, and 1 means stroke fully visible.
        self._stroke_opacity = 1

        # Width of the stroke of the shape
        self._stroke_width = 1

        # Red value of the fill color, should be integer between 0 and 255
        self._red_fill_color = 255

        # Green value of the fill color, should be integer between 0 and 255
        self._green_fill_color = 255

        # Blue value of the fill color, should be integer between 0 and 255
        self._blue_fill_color = 255

        # Fill opacity of the shape, between 0 and 1. 0 means fill invisible, and 1 means fill fully visible.
        self._fill_opacity = 1

        # List of keyframes of the shape, used to animate the shape.
        #
        # The keyframes are organized this way : each keyframe defines a time when an attribute should have a given
        # value. For each attribute, the animation interpolates the value of the attribute linearly between two
        # successive times (except for some attributes that cannot be interpolated such as a text or a font size).
        #
        # The keys attribute contains a map associating to a time a map containing pairs of attribute/value. Each pair,
        # associated with the key time is a keyframe of the animation. The pairs are sorted so that the "translateX" and
        # "translateY" appears first in each list.
        self._keyframes = defaultdict(dict)

        # Indicate if the pairs in the keyframe lists are sorted.
        self._sorted = True

        # Horizontal translate value of the shape.
        #
        # The translation is equivalent to the CSS translateX property.
        # Note that there is a major difference between moving a shape using the translation and moving it using the
        # specific coordinates attributes of the shape (for instance x of Rectangle class). The first one moves the
        # origin of the transformation with the object. The second one does not. This is important when the rotation
        # and scale transformations (rotate_z, scale_x, scale_y) are used, because they depends
        # on where the origin is.
        self._translate_x = 0

        # Vertical translate value of the shape.
        #
        # The translation is equivalent to the CSS translateY property.
        # Note that there is a major difference between moving a shape using the translation and moving it using the
        # specific coordinates attributes of the shape (for instance x of Rectangle class). The first one moves the
        # origin of the transformation with the object. The second one does not. This is important when the rotation
        # and scale transformations (rotate_z, scale_x, scale_y) are used, because they depends
        # on where the origin is.
        self._translate_y = 0

        # Rotate value of the shape.
        #
        # The rotation is equivalent to the CSS rotateZ property.
        # The origin of the rotation depends on the specific coordinates attributes of the shape (for instance
        # x of Rectangle class). Note that using the translate attributes moves the origin with the shape so that
        # it is possible to translate the shape and keep the same rotation effect.
        self._rotate_z = 0

        # Horizontal scale value of the shape.
        #
        # The scale is equivalent to the CSS scaleX property.
        # The origin of the scale depends on the specific coordinates attributes of the shape (for instance
        # x of Rectangle class). Note that using the translate attributes moves the origin with the shape so that
        # it is possible to translate the shape and keep the same scale effect.
        self._scale_x = 1
        
        # Vertical scale value of the shape.
        #
        # The scale is equivalent to the CSS scaleY property.
        # The origin of the scale depends on the specific coordinates attributes of the shape (for instance
        # x of Rectangle class). Note that using the translate attributes moves the origin with the shape so that
        # it is possible to translate the shape and keep the same scale effect.
        self._scale_y = 1

        # True if the shape belongs to a group and false otherwise.
        self._has_parent = False

    @property
    def name(self):
        """
        :return: the name of the SVG shape, used to define the id of the SVG tag, with the id attribute.
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        Set the name of the SVG shape, used to define the id of the SVG tag, with the id attribute.
        :param value:the name of the SVG shape
        """
        self._name = value

    @property
    def id(self):
        return self._id

    @staticmethod
    def reset_ids():
        Shape._last_id = 0

    @property
    def translate_x(self):
        """
        Return the horizontal translate value of the shape.
      
        The translation is equivalent to the CSS translateX property.
        Note that there is a major difference between moving a shape using the translation and moving it using the
        specific coordinates attributes of the shape (for instance x of Rectangle class). The first one moves the
        origin of the transformation with the object. The second one does not. This is important when the rotation
        and scale transformations (rotate_z, scale_x, scale_y) are used, because
        they depends on where the origin is.
      
        :return: the horizontal translate value of the shape.
        """
        return self._translate_x

    @translate_x.setter
    def translate_x(self, value):
        """
        Set the horizontal translate value of the shape.
      
        The translation is equivalent to the CSS translateX property.
        Note that there is a major difference between moving a shape using the translation and moving it using the
        specific coordinates attributes of the shape (for instance x of Rectangle class). The first one moves the
        origin of the transformation with the object. The second one does not. This is important when the rotation
        and scale transformations (rotate_z, scale_x, scale_y) are used, because
        they depends on where the origin is.
      
        :param value: the horizontal translate value of the shape.
        """
        self._translate_x = value

    @property
    def translate_y(self):
        """
        Return the vertical translate value of the shape.
      
        The translation is equivalent to the CSS translateY property.
        Note that there is a major difference between moving a shape using the translation and moving it using the
        specific coordinates attributes of the shape (for instance x of Rectangle class). The first one moves the
        origin of the transformation with the object. The second one does not. This is important when the rotation
        and scale transformations (rotate_z, scale_x, scale_y) are used, because
        they depends on where the origin is.
      
       :return: the vertical translate value of the shape.
        """
        return self._translate_y

    @translate_y.setter
    def translate_y(self, value):
        """
        Set the vertical translate value of the shape.
      
        The translation is equivalent to the CSS translateY property.
        Note that there is a major difference between moving a shape using the translation and moving it using the
        specific coordinates attributes of the shape (for instance x of Rectangle class). The first one moves the
        origin of the transformation with the object. The second one does not. This is important when the rotation
        and scale transformations (rotate_z, scale_x, scale_y) are used, because
        they depends on where the origin is.
      
        :param value: the vertical translate value of the shape.
        """
        self._translate_y = value

    @property
    def rotate_z(self):
        """
        Return the rotate value of the shape.
      
        The rotation is equivalent to the CSS rotateZ property.

        The origin of the rotation depends on the specific coordinates attributes of the shape (for instance
        x of Rectangle class). Note that using the translate attributes moves the origin with the shape so that
        it is possible to translate the shape and keep the same rotation effect.
      
       :return: the rotate value of the shape.
        """
        return self._rotate_z

    @rotate_z.setter
    def rotate_z(self, value):
        """
        Set the rotate value of the shape. The angle should be a string containing an angle in degree followed by 'deg'
        or an angle in radian followed by 'rad' or a number followed by turn. For instance '25deg', '1.5rad' or
        '0.7turn'. A turn is 360 degree.
      
        The rotation is equivalent to the CSS rotateZ property.
        The origin of the rotation depends on the specific coordinates attributes of the shape (for instance
        x of Rectangle class). Note that using the translate attributes moves the origin with the shape so that
        it is possible to translate the shape and keep the same rotation effect.
      
        :param value: the rotate value of the shape.
        """
        self._rotate_z = value

    @property
    def scale_x(self):
        """
        Return the horizontal scale value of the shape.
      
        The scale is equivalent to the CSS scaleX property.
        The origin of the scale depends on the specific coordinates attributes of the shape (for instance
        x of Rectangle class). Note that using the translate attributes moves the origin with the shape so that
        it is possible to translate the shape and keep the same scale effect.
      
       :return: the horizontal scale value of the shape.
        """
        return self._scale_x

    @scale_x.setter
    def scale_x(self, value):
        """
        Set the horizontal scale value of the shape.
      
        The scale is equivalent to the CSS scaleX property.
        The origin of the scale depends on the specific coordinates attributes of the shape (for instance
        x of Rectangle class). Note that using the translate attributes moves the origin with the shape so that
        it is possible to translate the shape and keep the same scale effect.
      
        :param value: the horizontal scale value of the shape.
        """
        self._scale_x = value

    @property
    def scale_y(self):
        """
        Return the vertical scale value of the shape.
      
        The scale is equivalent to the CSS scaleY property.
        The origin of the scale depends on the specific coordinates attributes of the shape (for instance
        x of Rectangle class). Note that using the translate attributes moves the origin with the shape so that
        it is possible to translate the shape and keep the same scale effect.
      
       :return: the vertical scale value of the shape.
        """
        return self._scale_y

    @scale_y.setter
    def scale_y(self, value):
        """
        Set the vertical scale value of the shape.
      
        The scale is equivalent to the CSS scaleY property.
        The origin of the scale depends on the specific coordinates attributes of the shape (for instance
        x of Rectangle class). Note that using the translate attributes moves the origin with the shape so that
        it is possible to translate the shape and keep the same scale effect.
      
        :param value: the vertical scale value of the shape.
        """
        self._scale_y = value

    @property
    def red_stroke_color(self):
        """
        :return: the red value of color of the stroke of the shape, integer between 0 and 255.
        """
        return self._red_stroke_color

    @red_stroke_color.setter
    def red_stroke_color(self, value):
        """
        Set the red value of the color of the stroke of the shape.
        The value should be an integer between 0 and 255. If a float value is given, it is rounded.
        If an integer out of the bounds is given, set it to the closest bound
        :param value: the red value of the color of the stroke of the shape
        """
        value = int(value)
        if value < 0:
            value = 0
        if value > 255:
            value = 255
        self._red_stroke_color = value

    @property
    def green_stroke_color(self):
        """
        :return: the green value of color of the stroke of the shape, integer between 0 and 255.
        """
        return self._green_stroke_color

    @green_stroke_color.setter
    def green_stroke_color(self, value):
        """
        Set the green value of the color of the stroke of the shape.
        The value should be an integer between 0 and 255. If a float value is given, it is rounded.
        If an integer out of the bounds is given, set it to the closest bound
        :param value: the green value of the color of the stroke of the shape
        """
        value = int(value)
        if value < 0:
            value = 0
        if value > 255:
            value = 255
        self._green_stroke_color = value

    @property
    def blue_stroke_color(self):
        """
        :return: the blue value of color of the stroke of the shape, integer between 0 and 255.
        """
        return self._blue_stroke_color

    @blue_stroke_color.setter
    def blue_stroke_color(self, value):
        """
        Set the blue value of the color of the stroke of the shape.
        The value should be an integer between 0 and 255. If a float value is given, it is rounded.
        If an integer out of the bounds is given, set it to the closest bound
        :param value: the blue value of the color of the stroke of the shape
        """
        value = int(value)
        if value < 0:
            value = 0
        if value > 255:
            value = 255
        self._blue_stroke_color = value

    @property
    def stroke_color(self):
        """
        :return: a tuple containing the red, the green and the blue values of color of the stroke of the shape,
        integers between 0 and 255.
        """
        return self.red_stroke_color, self.green_stroke_color, self.blue_stroke_color

    @stroke_color.setter
    def stroke_color(self, value):
        """
        Set the red, green and blue values of the color of the stroke of the shape.
        The values should be integers between 0 and 255. If a float value is given, it is rounded.
        If an integer out of the bounds is given, set it to the closest bound
        :param value: a tuple of 3 values, the red, green and blue values of the color of the stroke of the shape
        """
        self.red_stroke_color, self.green_stroke_color, self.blue_stroke_color = value

    def _get_stroke_color(self):
        """
        :return: an hexadecimal string corresponding to the stroke color of the shape
        """
        return '#{:02x}{:02x}{:02x}'.format(*self.stroke_color)

    def _set_stroke_color(self, value):
        """
        Set the stroke color of the shape
        :param value: an hexadecimal string corresponding to the stroke color of the shape
        """
        value = value.lstrip('#')
        self.stroke_color = tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

    @property
    def stroke_width(self):
        """
        :return: the width of the stroke of the shape
        """
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value):
        """
        Set the width of the stroke of the shape
        :param value: the width of the stroke of the shape
        """
        self._stroke_width = value

    @property
    def stroke_opacity(self):
        """
        :return: the opacity of the stroke of the shape, between 0 and 1. 0 means invisible, and 1 means
        fully visible.
        """
        return self._stroke_opacity

    @stroke_opacity.setter
    def stroke_opacity(self, value):
        """
        Set the opacity of the stroke of the shape, between 0 and 1. 0 means invisible, and 1 means fully visible.
        :param value: the opacity of the stroke of the shape
        """
        self._stroke_opacity = value

    @property
    def red_fill_color(self):
        """
        :return: the red value of color of the fill of the shape, integer between 0 and 255.
        """
        return self._red_fill_color

    @red_fill_color.setter
    def red_fill_color(self, value):
        """
        Set the red value of the color of the fill of the shape.
        The value should be an integer between 0 and 255. If a float value is given, it is rounded.
        If an integer out of the bounds is given, set it to the closest bound
        :param value: the red value of the color of the fill of the shape
        """
        value = int(value)
        if value < 0:
            value = 0
        if value > 255:
            value = 255
        self._red_fill_color = value

    @property
    def green_fill_color(self):
        """
        :return: the green value of color of the fill of the shape, integer between 0 and 255.
        """
        return self._green_fill_color

    @green_fill_color.setter
    def green_fill_color(self, value):
        """
        Set the green value of the color of the fill of the shape.
        The value should be an integer between 0 and 255. If a float value is given, it is rounded.
        If an integer out of the bounds is given, set it to the closest bound
        :param value: the green value of the color of the fill of the shape
        """
        value = int(value)
        if value < 0:
            value = 0
        if value > 255:
            value = 255
        self._green_fill_color = value

    @property
    def blue_fill_color(self):
        """
        :return: the blue value of color of the fill of the shape, integer between 0 and 255.
        """
        return self._blue_fill_color

    @blue_fill_color.setter
    def blue_fill_color(self, value):
        """
        Set the blue value of the color of the fill of the shape.
        The value should be an integer between 0 and 255. If a float value is given, it is rounded.
        If an integer out of the bounds is given, set it to the closest bound
        :param value: the blue value of the color of the fill of the shape
        """
        value = int(value)
        if value < 0:
            value = 0
        if value > 255:
            value = 255
        self._blue_fill_color = value

    @property
    def fill_color(self):
        """
        :return: a tuple containing the red, the green and the blue values of color of the fill of the shape,
        integers between 0 and 255.
        """
        return self.red_fill_color, self.green_fill_color, self.blue_fill_color

    @fill_color.setter
    def fill_color(self, value):
        """
        Set the red, green and blue values of the color of the fill of the shape.
        The values should be integers between 0 and 255. If a float value is given, it is rounded.
        If an integer out of the bounds is given, set it to the closest bound
        :param value: a tuple of 3 values, the red, green and blue values of the color of the fill of the shape
        """
        self.red_fill_color, self.green_fill_color, self.blue_fill_color = value

    def _get_fill_color(self):
        """
        :return: an hexadecimal string corresponding to the fill color of the shape
        """
        return '#{:02x}{:02x}{:02x}'.format(*self.fill_color)

    def _set_fill_color(self, value):
        """
        Set the fill color of the shape
        :param value: an hexadecimal string corresponding to the fill color of the shape
        """
        value = value.lstrip('#')
        self.fill_color = tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

    @property
    def fill_opacity(self):
        """
        :return: the opacity of the fill of the shape, between 0 and 1. 0 means invisible, and 1 means
        fully visible.
        """
        return self._fill_opacity

    @fill_opacity.setter
    def fill_opacity(self, value):
        """
        Set the opacity of the stroke of the shape, between 0 and 1. 0 means invisible, and 1 means fully visible.
        :param value: the opacity of the stroke of the shape
        """
        self._fill_opacity = value

    @property
    def opacity(self):
        """
        :return: the opacity of the stroke and the fill of the shape, between 0 and 1. 0 means invisible, and 1 means
        fully visible.
        """
        return self._stroke_opacity, self._fill_opacity

    @opacity.setter
    def opacity(self, value):
        """
        Set the opacity of the shape, between 0 and 1. 0 means invisible, and 1 means fully visible.
        :param value: the opacity of the shape
        """
        self._stroke_opacity = value
        self._fill_opacity = value

    @property
    def has_parent(self):
        return self._has_parent

    def set_has_parent(self):
        self._has_parent = True

    def save_state(self, turn):
        """
            Save the keyframe containing all the attributes of the shape.
        
            Each keyframe defines a time when an attribute should have a given value.
            For each attribute, the animation interpolates the value of the attribute linearly between two successive
            times (except for some attributes that cannot be interpolated such as a text or a font size).
        
            Saving the state means that, at the given turn, the animation should set every attribute to the value saved
            in the keyframe. The turn is not an integer. It is possible to save a state at the "turn" 4.5 : at midtime
            between turn 4 and turn 5.
        
            :param turn : turn during which the keyframe occurs
        """
        self._save_translate(turn)
        self._save_rotate(turn)
        self._save_scale(turn)
        self._save_opacity(turn)
        self._save_fill_and_stroke(turn)

    def load_state(self, turn):
        """
           Load the keyframe containing all the attributes of the shape. Every attributes takes the value of the
           corresponding keyframe. If the attribute is not registered in the keyframe, the value is unchanged.
           :param turn : turn during which the keyframe occurs
        :param turn:
        """
        self._load_translate(turn)
        self._load_rotate(turn)
        self._load_scale(turn)
        self._load_opacity(turn)
        self._load_fill_and_stroke(turn)

    def _save_translate(self, turn):
        """
           Save the keyframe containing the attributes corresponding to the translation of the shape
           :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'translateX', self.translate_x)
        self._add_key_frame(turn, 'translateY', self.translate_y)

    def _load_translate(self, turn):
        """
           Load the keyframe containing the attributes corresponding to the translation of the shape
           :param turn : turn during which the keyframe occurs
        """
        tx = int(self._get_key_frame(turn, 'translateX'))
        if tx is not None:
            self.translate_x = tx
        ty = int(self._get_key_frame(turn, 'translateY'))
        if ty is not None:
            self.translate_y = ty

    def _save_rotate(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the rotation of the shape
        :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'rotateZ', self.rotate_z)

    def _load_rotate(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the rotation of the shape
        :param turn : turn during which the keyframe occurs
        """
        rz = float(self._get_key_frame(turn, 'rotateZ'))
        if rz is not None:
            self.rotate_z = rz

    def _save_scale(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the scale of the shape
        :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'scaleX', self.scale_x)
        self._add_key_frame(turn, 'scaleY', self.scale_y)

    def _load_scale(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the scale of the shape
        :param turn : turn during which the keyframe occurs
        """
        sx = float(self._get_key_frame(turn, 'scaleX'))
        if sx is not None:
            self.scale_x = sx
        sy = float(self._get_key_frame(turn, 'scaleY'))
        if sy is not None:
            self.scale_y = sy

    def _save_fill_and_stroke(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the fill color and the stroke of the shape
        :param turn : turn during which the keyframe occurs

        """
        self._add_key_frame(turn, 'fill', self._get_fill_color())
        self._add_key_frame(turn, 'stroke', self._get_stroke_color())
        self._add_key_frame(turn, 'strokeWidth', self.stroke_width)

    def _load_fill_and_stroke(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the fill color and the stroke of the shape
        :param turn : turn during which the keyframe occurs
        """
        cf = str(self._get_key_frame(turn, 'fill'))
        if cf is not None:
            self._set_fill_color(cf)
        cs = str(self._get_key_frame(turn, 'stroke'))
        if cs is not None:
            self._set_stroke_color(cs)
        sw = int(self._get_key_frame(turn, 'strokeWidth'))
        if sw is not None:
            self.stroke_width = sw

    def _save_opacity(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the opacity of the shape
        :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'stroke-opacity', self.stroke_opacity)
        self._add_key_frame(turn, 'fill-opacity', self.fill_opacity)

    def _load_opacity(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the opacity of the shape
        :param turn : turn during which the keyframe occurs
        """
        op = float(self._get_key_frame(turn, 'stroke-opacity'))
        if op is not None:
            self.stroke_opacity = op
        op = float(self._get_key_frame(turn, 'fill-opacity'))
        if op is not None:
            self.fill_opacity = op

    @property
    def keyframes(self):
        """
        Return the list of keyframes of the shape, used to animate the shape.
      
        The keyframes are organized this way : each keyframe defines a time when an attribute should have a given value.
        For each attribute, the animation interpolates the value of the attribute linearly between two successive times
        (except for some attributes that cannot be interpolated such as a text or a font size).
      
        The keys attribute contains a map associating to a time a map containing pairs of attribute/value. Each pair,
        associated with the key time is a keyframe of the animation.
      
        :return:the list of keyframes of the shape, used to animate the shape.
        """
        if not self._sorted:

            # For each dict in the values of self._keyframes, sort that dict so that TranslateX and TranslateY are
            # sorted first
            for key in self._keyframes.keys():
                keywords_key = get_keyword_key()
                self._keyframes[key] = dict(sorted(self._keyframes[key].items(),
                                                   key=lambda keyvalue: keywords_key(keyvalue[0])))

            # Sort by key
            self._keyframes = dict(sorted(self._keyframes.items()))
            self._sorted = True

        return self._keyframes

    def _add_key_frame(self, turn, attribute_name, value):
        """
        Add a new keyframe to the shape. The attribute defines by the corresponding attributeName should have the given
        value at the given turn. The turn is not an integer. It is possible to save a state at the "turn" 4.5 : at
        midtime between turn 4 and turn 5.
      
        :param turn : turn during which the keyframe occurs
        :param attribute_name : name of the attribute set by the keyframe
        :param value : value that the attribute should have at the given turn
        """
        self._sorted = False
        self._keyframes[turn][attribute_name] = value

    def _get_key_frame(self, turn, attribute_name):
        """
        :param turn : turn during which a keyframe occurs
        :param attribute_name : name of the attribute for which we want to know the value of the keyframe
        :return:the value associated with the given attribute (defined by the given name) in the keyframe of the
        given turn.
        """
        return self._keyframes[turn][attribute_name]

    @abstractmethod
    def tag_svg(self):
        """
        :return: the SVG tag associated with this shape.
        """
        pass

    @abstractmethod
    def attributes_svg(self):
        """
        :return: a string representing the attributes of the SVG tag of this shape, as they should be written in an SVG
        file.
        """
        pass

    def get_content(self):
        """
        Build and return the content that should be inserted between the opening and the closing tag of the SVG shape.
        Mostly for the text shape in which the content is the displayed text. If the string is null, the content is
        empty.
        :return: the content of the SVG shape
        """
        return None

    def to_svg(self):
        """
        Build the SVG objet containing the tag, the attributes and the content representing this shape on the
        following model: <tag attributes>content</tag> if the content is not empty and <tag attributes/> otherwise.
        :return: the built SVG object.
        """

        try:
            # Get the value of the first turn and put the shape in the state of that turn
            first_turn = list(self.keyframes.keys())[0]
            self.load_state(first_turn)
        except IndexError:
            # If no such turn exists, it means there is no animation for this shape
            # In that case we do nothing, the shape is already in the right state.
            pass
        
        tag = self.tag_svg()

        # Build the beginning part of the object
        s = ("<%s %s id=\"%s\" stroke=\"%s\" stroke-width=\"%d\" fill=\"%s\" "
             "stroke-opacity=\"%.2f\" fill-opacity=\"%.2f\" ") % (
                tag,
                self.attributes_svg(),
                self.name + str(self.id),
                self._get_stroke_color(),
                self.stroke_width,
                self._get_fill_color(),
                self.stroke_opacity,
                self.fill_opacity)

        # Write the content of the object or close the tag if no such content exists
        content = self.get_content()
        if content is None:
            s += '/>'
        else:
            s += '>\n'
            s += content + '\n'
            s += '</%s>' % tag
            
        return s

    def to_animation(self):
        """
        Build the list of all the keyframes of the shape.
      
        The keyframes are organized this way : each keyframe defines a time when an attribute should have a given value.
        For each attribute, the animation interpolates the value of the attribute linearly between two successive times
        (except for some attributes that cannot be interpolated such as a text or a font size). The attributes are
        sorted so that the "translateX" and "translateY" attributes appears first to ensure the translation animation is
        done first.
      
        The keyframes are saved using the save_state(turn) method, which builds a keyframe containing all the
        attributes of the shape.
        The list of keyframes are sorted by time, and grouped by the floor values of the times (times 3.4 and 3.8 are
        in the same group, 3.8 and 4.2 are not).
      
        The returned object is a list of map. The list contains one map per group. Each map then associate, for each
        time value of the keyframes, the fractional part of the time to the map (attribute - value) of the keyframe. If,
        in two successive keyframes (of a same group or not), the value of an attribute is unchanged, the attribute is
        removed from the second keyframe. An empty keyframe means that nothing changed from the previous keyframe and
        that the animation should be constant between those two keyframes. 
      
        :return:the list of all the keyframes of the shape.
        """
        # If no animation is set, we save one state that will be returned
        if len(self._keyframes) == 0:
            self.save_state(1)

        # We get the items (sorted turn by turn)
        items = list(self.keyframes.items())

        # List of animations to be returned
        animations = []

        # Get the first item and the turn of that item
        first_item = items.pop(0)
        current_turn = first_item[0]
        current_turn_round = int(current_turn)

        pruned_keys = dict()
        animations.append(pruned_keys)

        # The dict of animations where we do not repeat the keyword if nothing changes since the last key
        pruned_keys['0.0'] = first_item[1]

        if current_turn != 1 and current_turn_round != 1:
            # If the first registered turn is not the turn 1,
            # we pad the first turns with None
            if len(animations) == 0:
                animations.append(None)
            for i in range(2, current_turn_round):
                animations.append(None)

            pruned_keys = dict()
            if current_turn != current_turn_round:
                pruned_keys[current_turn - current_turn_round] = dict()
            animations.append(pruned_keys)
        elif current_turn != 1:
            # The first animation starts at 1.XX.
            if len(animations) == 0:
                animations.append(pruned_keys)
            pruned_keys[current_turn - current_turn_round] = dict()

        last_item = first_item
        for turn, state in items:
            #
            turn_round = int(turn)
            if current_turn_round < turn_round:
                while current_turn_round < turn_round - 1:
                    # Pad the previous turns with None
                    current_turn_round += 1
                    animations.append(None)
                current_turn_round += 1
                pruned_keys = dict()
                animations.append(pruned_keys)

            # Compute the state of the turn by filtering the attributes not changing
            pruned_state = dict()
            for attribute, value in state.items():
                # We check if the value of the attribute changed since last turn

                if last_item[1][attribute] == value:
                    continue
                pruned_state[attribute] = value

            # If nothing changed, we do nothing
            if len(pruned_state) != 0 or turn != turn_round:
                pruned_keys[turn - turn_round] = pruned_state
            last_item = (turn, state)
        return animations


class Group(Shape):
    """
        Shape representing a SVG group
       
        A Group is a complex shape containing children shapes.
        Once a shape is attached to a group, every transformation performed on the group is transmitted to the children.
        Every transformation performed on the child is performed only on the child, but related to the coordinate system
        of the group.
       
        The origin point of the rotations and scaling performed on the group is at the origin point (0, 0).
        This origin point can be moved by translating the group using {@link #setTranslateX(int)} and
        {@link #setTranslateY(int)}. Note that translating the group means also translating the children of the group.
        However, translating a child or moving it using the specific coordinates attributes of the shape (for instance
        (for instance {@link Rectangle#getX()}) does not move the origin point of the group. This way it is possible
        to place every object relative to the origin point in order to perform the right transformations of the group.
       
        For instance, let g be a group  containing a horizontal line and a rectangle.
    """
    
    def __init__(self, name):
        """
         Build a new group with no child.
         :param name : name of the SVG group, used to define the id of the SVG tag.
        """

        super().__init__(name)

        # List of shapes belonging to the group.
        self._children = []

    def add_child(self, child):
        """
        Add the given shape to the list of children of the group.
           
        The child may be a group but this group should not be a descendant of the given child, in order to
        prevent circular dependencies (for instance a group containing itself). In that case, the child is not added to
        the group.
           
        :param child : a shape added to this group.
        """
        if type(child) is Group:
            if child.has_descendant(self):
                return
        self._children.append(child)
        child.set_has_parent()

    def add_children(self, children):
        """
           Add the given shapes to the list of children of the group.
           
           The children may be groups but this group should not be a descendant of any of the given children, in order
           to prevent circular dependencies (for instance a group containing itself). The children not satisfying this
           constraint are not added to the group.
           
        :param children : a list of shapes added to this group
        """
        for child in children:
            self.add_child(child)

    def has_descendant(self, shape):
        """
        :param shape
        :return: true if the given shape is a descendant of this group (a child or a descendant of a group child)
        """
        for child in self._children:
            if child == shape:
                return True
            if type(child) is Group and child.has_descendant(shape):
                return True

    def tag_svg(self):
        return 'g'

    def attributes_svg(self):
        return ""

    def get_content(self):
        return ''.join([child.to_svg() for child in self._children])

    def save_state(self, turn):
        super().save_state(turn)
        for child in self._children:
            child.save_state(turn)

    def load_state(self, turn):
        super().load_state(turn)
        for child in self._children:
            child.load_state(turn)

    @property
    def children(self):
        """
        :return: the list of children of the shape 
        """
        return iter(self._children)

    @property
    def red_stroke_color(self):
        return self._red_stroke_color

    @property
    def green_stroke_color(self):
        return self._green_stroke_color

    @property
    def blue_stroke_color(self):
        return self._blue_stroke_color

    @red_stroke_color.setter
    def red_stroke_color(self, value):
        self._red_stroke_color = value
        for child in self._children:
            child.red_stroke_color = value

    @green_stroke_color.setter
    def green_stroke_color(self, value):
        self._green_stroke_color = value
        for child in self._children:
            child.green_stroke_color = value

    @blue_stroke_color.setter
    def blue_stroke_color(self, value):
        self._blue_stroke_color = value
        for child in self._children:
            child.blue_stroke_color = value

    @property
    def stroke_width(self):
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value):
        self._stroke_width = value
        for child in self._children:
            child.stroke_width = value

    @property
    def red_fill_color(self):
        return self._red_fill_color

    @property
    def green_fill_color(self):
        return self._green_fill_color

    @property
    def blue_fill_color(self):
        return self._blue_fill_color

    @red_fill_color.setter
    def red_fill_color(self, value):
        self._red_fill_color = value
        for child in self._children:
            child.red_fill_color = value

    @green_fill_color.setter
    def green_fill_color(self, value):
        self._green_fill_color = value
        for child in self._children:
            child.green_fill_color = value

    @blue_fill_color.setter
    def blue_fill_color(self, value):
        self._blue_fill_color = value
        for child in self._children:
            child.blue_fill_color = value

    @property
    def stroke_opacity(self):
        """
        :return: the opacity of the stroke of the shape, between 0 and 1. 0 means invisible, and 1 means
        fully visible.
        """
        return self._stroke_opacity

    @stroke_opacity.setter
    def stroke_opacity(self, value):
        """
        Set the opacity of the stroke of the shape, between 0 and 1. 0 means invisible, and 1 means fully visible.
        :param value: the opacity of the stroke of the shape
        """
        self._stroke_opacity = value
        for child in self._children:
            child.stroke_opacity = value

    @property
    def fill_opacity(self):
        """
        :return: the opacity of the fill of the shape, between 0 and 1. 0 means invisible, and 1 means
        fully visible.
        """
        return self._fill_opacity

    @fill_opacity.setter
    def fill_opacity(self, value):
        """
        Set the opacity of the fill of the shape, between 0 and 1. 0 means invisible, and 1 means fully visible.
        :param value: the opacity of the stroke of the shape
        """
        self._fill_opacity = value
        for child in self._children:
            child.fill_opacity = value

    @property
    def opacity(self):
        """
        :return: the opacity of the stroke and the fill of the shape, between 0 and 1. 0 means invisible, and 1 means
        fully visible.
        """
        return self._stroke_opacity, self._fill_opacity

    @opacity.setter
    def opacity(self, value):
        """
        Set the opacity of the shape, between 0 and 1. 0 means invisible, and 1 means fully visible.
        :param value: the opacity of the shape
        """
        self._stroke_opacity = value
        self._fill_opacity = value
        for child in self._children:
            child.opacity = value


class Line(Shape):
    """
    Shape representing a SVG line
    """
    def __init__(self, name, x1, y1, x2, y2):
        """
        Build a new line
        :param name: name of the SVG shape of the path, used to define the id of the SVG tag.
        :param x1: Abcissa of the first point of the line
        :param y1: Ordinate of the first point of the line
        :param x2: Abcissa of the second point of the line
        :param y2: Ordinate of the second point of the line
        """

        super().__init__(name)

        self._x1 = x1
        self._y1 = y1
        self._x2 = x2
        self._y2 = y2

    @property
    def x1(self):
        """
        :return: the abcissa of the first point of the line
        """
        return self._x1

    @x1.setter
    def x1(self, value):
        """
        Set the abcissa of the first point of the line
        :param value: abcissa of the first point of the line
        """
        self._x1 = value

    @property
    def y1(self):
        """
        :return: the ordinate of the first point of the line
        """
        return self._y1

    @y1.setter
    def y1(self, value):
        """
        Set the ordinate of the first point of the line
        :param value: ordinate of the first point of the line
        """
        self._y1 = value

    @property
    def x2(self):
        """
        :return: the abcissa of the second point of the line
        """
        return self._x2

    @x2.setter
    def x2(self, value):
        """
        Set the abcissa of the second point of the line
        :param value: abcissa of the second point of the line
        """
        self._x2 = value

    @property
    def y2(self):
        """
        :return: the ordinate of the second point of the line
        """
        return self._y2

    @y2.setter
    def y2(self, value):
        """
        Set the ordinate of the second point of the line
        :param value: ordinate of the second point of the line
        """
        self._y2 = value

    def save_state(self, turn):
        super().save_state(turn)
        self._save_p1(turn)
        self._save_p2(turn)

    def load_state(self, turn):
        super().load_state(turn)
        self._load_p1(turn)
        self._load_p2(turn)

    def _save_p1(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the first point of the line
        :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'x1', self.x1)
        self._add_key_frame(turn, 'y1', self.y1)

    def _load_p1(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the first point of the line
        :param turn : turn during which the keyframe occurs
        """
        x1 = int(self._get_key_frame(turn, 'x1'))
        if x1 is not None:
            self.x1 = x1
        y1 = int(self._get_key_frame(turn, 'y1'))
        if y1 is not None:
            self.y1 = y1

    def _save_p2(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the second point of the line
        :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'x2', self.x2)
        self._add_key_frame(turn, 'y2', self.y2)

    def _load_p2(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the second point of the line
        :param turn : turn during which the keyframe occurs
        """
        x2 = int(self._get_key_frame(turn, 'x2'))
        if x2 is not None:
            self.x2 = x2
        y2 = int(self._get_key_frame(turn, 'y2'))
        if y2 is not None:
            self.y2 = y2

    def tag_svg(self):
        return 'line'

    def attributes_svg(self):
        return "x1=\"%d\" y1=\"%d\" x2=\"%d\" y2=\"%d\"" % (self.x1, self.y1, self.x2, self.y2)


class Oval(Shape):
    """
    Shape representing a SVG ellipse/circle
    """

    def __init__(self, name, cx, cy, rx, ry):
        """
         Build a new oval
        :param name: name of the SVG shape of the path, used to define the id of the SVG tag.
        :param cx: Abscissa of the center of the oval
        :param cy: Ordinate of the center of the oval
        :param rx: x-radius of the oval
        :param ry: y-radius of the oval
        """
        super().__init__(name)

        self._cx = cx
        self._cy = cy
        self._rx = rx
        self._ry = ry

    @property
    def cx(self):
        """
        :return: the abscissa of the center of the oval
        """
        return self._cx

    @cx.setter
    def cx(self, value):
        """
         Set the abscissa of the center of the oval
         :param value : abscissa of the center of the oval
        """
        self._cx = value

    @property
    def cy(self):
        """
        :return: the ordinate of the center of the oval
        """
        return self._cy

    @cy.setter
    def cy(self, value):
        """
         Set the ordinate of the center of the oval
         :param value : ordinate of the center of the oval
        """
        self._cy = value

    @property
    def rx(self):
        """
         :return: the x-radius of the oval
        """
        return self._rx

    @rx.setter
    def rx(self, value):
        """
         Set the x-radius of the oval
         :param value : x-radius of the oval
        """
        self._rx = value

    @property
    def ry(self):
        """
         :return: the y-radius of the oval
        """
        return self._ry

    @ry.setter
    def ry(self, value):
        """
         Set the y-radius of the oval
         :param value : y-radius of the oval
        """
        self._ry = value

    def save_state(self, turn):
        super().save_state(turn)
        self._save_center(turn)
        self._save_radius(turn)

    def load_state(self, turn):
        super().load_state(turn)
        self._load_center(turn)
        self._load_radius(turn)

    def _save_center(self, turn):
        """
         Save the keyframe containing the attributes corresponding to the center of the oval
         :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'cx', self.cx)
        self._add_key_frame(turn, 'cy', self.cy)

    def _save_radius(self, turn):
        """
         Save the keyframe containing the attributes corresponding to the radius of the oval
         :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'rx', self.rx)
        self._add_key_frame(turn, 'ry', self.ry)

    def _load_center(self, turn):
        """
         Load the keyframe containing the attributes corresponding to the center of the oval
         :param turn : turn during which the keyframe occurs
        """
        cx = int(self._get_key_frame(turn, 'cx'))
        if cx is not None:
            self.cx = cx
        cy = int(self._get_key_frame(turn, 'cy'))
        if cy is not None:
            self.cy = cy

    def _load_radius(self, turn):
        """
         Load the keyframe containing the attributes corresponding to the radius of the oval
         :param turn : turn during which the keyframe occurs
        """
        rx = int(self._get_key_frame(turn, 'rx'))
        if rx is not None:
            self.rx = rx
        ry = int(self._get_key_frame(turn, 'ry'))
        if ry is not None:
            self.ry = ry

    def tag_svg(self):
        return 'ellipse'

    def attributes_svg(self):
        return "cx=\"%d\" cy=\"%d\" rx=\"%d\" ry=\"%d\"" % (
            self.cx,
            self.cy,
            self.rx,
            self.ry)


class Rectangle(Shape):
    """
    Shape representing a SVG rectangle
    """

    def __init__(self, name, x, y, width, height, rx=0, ry=0):
        """
        :param name: name of the SVG shape of the path, used to define the id of the SVG tag.
        :param x: Abcissa of the top left corner of the rectangle
        :param y: Ordinate of the top left corner of the rectangle
        :param width: Width of the rectangle
        :param height: Height of the rectangle
        :param rx: x-radius of the corners of the rectangle, if 0, the corners are not rounded
        :param ry: y-radius of the corners of the rectangle, if 0, the corners are not rounded
        """
        super().__init__(name)
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._rx = rx
        self._ry = ry

    @property
    def x(self):
        """
        :return: the abscissa of the top left corner of the rectangle
        """
        return self._x

    @x.setter
    def x(self, value):
        """
         Set the abscissa of the top left corner of the rectangle
         :param value : abscissa of the top left corner of the rectangle
        """
        self._x = value

    @property
    def y(self):
        """
        :return: the ordinate of the top left corner of the rectangle
        """
        return self._y

    @y.setter
    def y(self, value):
        """
         Set the ordinate of the top left corner of the rectangle
         :param value : ordinate of the top left corner of the rectangle
        """
        self._y = value

    @property
    def width(self):
        """
        :return: the width of the rectangle
        """
        return self._width

    @width.setter
    def width(self, value):
        """
         Set the width of the rectangle
         :param value : the width of the rectangle
        """
        self._width = value

    @property
    def height(self):
        """
        :return: the height of the rectangle
        """
        return self._height

    @height.setter
    def height(self, value):
        """
         Set the height of the rectangle
         :param value : the height of the rectangle
        """
        self._height = value

    @property
    def rx(self):
        """
         :return: the x-radius of the oval
        """
        return self._rx

    @rx.setter
    def rx(self, value):
        """
         Set the x-radius of the oval
         :param value : x-radius of the oval
        """
        self._rx = value

    @property
    def ry(self):
        """
         :return: the y-radius of the oval
        """
        return self._ry

    @ry.setter
    def ry(self, value):
        """
         Set the y-radius of the oval
         :param value : y-radius of the oval
        """
        self._ry = value

    def save_state(self, turn):
        super().save_state(turn)
        self._save_upper_left_point(turn)
        self._save_dimensions(turn)
        self._save_rounded_corners(turn)

    def load_state(self, turn):
        super().load_state(turn)
        self._load_upper_left_point(turn)
        self._load_dimensions(turn)
        self._load_rounded_corners(turn)

    def _save_upper_left_point(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the upper left corner of the rectangle
         :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'x', self.x)
        self._add_key_frame(turn, 'y', self.y)

    def _load_upper_left_point(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the upper left corner of the rectangle
         :param turn : turn during which the keyframe occurs
        """
        x = int(self._get_key_frame(turn, 'x'))
        if x is not None:
            self.x = x
        y = int(self._get_key_frame(turn, 'y'))
        if y is not None:
            self.y = y

    def _save_dimensions(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the dimensions of the rectangle
         :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'width', self.width)
        self._add_key_frame(turn, 'height', self.height)

    def _load_dimensions(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the dimensions of the rectangle
         :param turn : turn during which the keyframe occurs

        """
        width = int(self._get_key_frame(turn, 'width'))
        if width is not None:
            self.width = width
        height = int(self._get_key_frame(turn, 'height'))
        if height is not None:
            self.height = height

    def _save_rounded_corners(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the rounded corners of the rectangle
         :param turn : turn during which the keyframe occurs

        """
        self._add_key_frame(turn, 'rx', self.rx)
        self._add_key_frame(turn, 'ry', self.ry)

    def _load_rounded_corners(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the rounded corners of the rectangle
         :param turn : turn during which the keyframe occurs
        """
        rx = int(self._get_key_frame(turn, 'rx'))
        if rx is not None:
            self.rx = rx
        ry = int(self._get_key_frame(turn, 'ry'))
        if ry is not None:
            self.ry = ry

    def tag_svg(self):
        return 'rect'

    def attributes_svg(self):
        return "x=\"%d\" y=\"%d\" width=\"%d\" height=\"%d\" rx=\"%d\" ry=\"%d\"" % (
            self.x, self.y, self.width, self.height, self.rx, self.ry
        )


class PolyLine(Shape):
    def __init__(self, name, closed, coordinates):
        super().__init__(name)

        # True if the path is closed (the last and the first points are linked), in that case, the polyline is a
        # polygone.
        self._closed = closed

        # List of all the coordinates of the points of the polyline.
        # Start with the x of the first point, then the y, then the x of the second point, the y of the second
        # point, ...
        self._coordinates = coordinates

    @property
    def closed(self):
        """
        :return: true if and only if the line is closed
        """
        return self._closed

    @closed.setter
    def closed(self, value):
        """
        Set the fact that the polyline is closed (and is then a polygon)
        :param value : true if the path should be closed
        """
        self._closed = value

    @property
    def coordinates(self):
        """
        return a view to the list of coordinates of the polyline. Modifying this list also edit the list of polyline.
        :return: the list of coordinates of the polyline
        """
        return self._coordinates

    @coordinates.setter
    def coordinates(self, value):
        """
        Set the list of coordinates of the polyline
        :param value : list of coordinates of the polyline
        """
        self._coordinates = value

    @property
    def coordinates_str(self):
        """
        :return: all the pairs of coordinates joined with ", "
        """
        return '  '.join('%d,%d' % (x, y) for x, y in zip(self._coordinates[::2], self._coordinates[1::2]))

    def save_state(self, turn):
        super().save_state(turn)
        self._save_coordinates(turn)

    def load_state(self, turn):
        super().load_state(turn)
        self._load_coordinates(turn)

    def _save_coordinates(self, turn):
        """
         Save the keyframe containing the attributes corresponding to the coordinates list
         :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'points', self.coordinates_str)

    def _load_coordinates(self, turn):
        """
         Load the keyframe containing the attributes corresponding to the coordinates list
         :param turn : turn during which the keyframe occurs
        """
        coords = str(self._get_key_frame(turn, 'points'))
        if coords is None:
            return
        self.coordinates = [int(x) for x in re.split(r'[, ]', coords) if re.match(r'-?\d+', x)]

    def tag_svg(self):
        return 'polygon' if self.closed else 'polyline'

    def attributes_svg(self):
        return 'points="%s"' % self.coordinates_str


class RegularePolygon(PolyLine):
    """
    Class representing a regular polygon through a polygon
    Once the polygon is created, the coordinates should be manipulated with the PolyLine methods
    """

    def __init__(self, name, cx, cy, radius, nb_edges):
        """
        Build a new regular polygon
        :param name: name of the SVG shape of the path, used to define the id of the SVG tag.
        :param cx: Abscissa of the center of the polygon
        :param cy: Ordinate of the center of the polygon
        :param radius: radius of the polygon
        :param nb_edges: number of edges of the polygon
        """
        coords = [cx, cy - radius]

        alpha = 2 * math.pi / nb_edges
        for i in range(1, nb_edges):
            angle = -math.pi / 2 + i * alpha
            coords.append(cx + radius * math.cos(angle))
            coords.append(cy + radius * math.sin(angle))
        super().__init__(name, True, coords)


class RegulareStar(PolyLine):
    """
    Class representing a regular star through a polygon
    Once the polygon is created, the coordinates should be manipulated with the PolyLine methods
    """

    def __init__(self, name, cx, cy, radius_int, radius_out, nb_sides):
        """
        Build a new regular polygon
        :param name: name of the SVG shape of the path, used to define the id of the SVG tag.
        :param cx: Abscissa of the center of the polygon
        :param cy: Ordinate of the center of the polygon
        :param radius_int: distance from the center to the interior angles of the star
        :param radius_out: distance from the center to the tips of the star
        :param nb_sides: number of sides of the star
        """
        coords = [cx, cy - radius_out]

        alpha = 2 * math.pi / (2 * nb_sides)
        for i in range(1, 2 * nb_sides):
            angle = -math.pi / 2 + i * alpha
            radius = radius_out if i % 2 == 0 else radius_int
            coords.append(cx + radius * math.cos(angle))
            coords.append(cy + radius * math.sin(angle))

        super().__init__(name, True, coords)


class Triangle(PolyLine):
    """
    Class representing a triangle through a polygon
    Once the triangle is created, the coordinates should be manipulated with the PolyLine methods
    """

    def __init__(self, name, x1, y1, x2, y2, x3, y3):
        """
        Create a new triangle
        """
        super().__init__(name, True, [x1, y1, x2, y2, x3, y3])


class Text(Shape):
    """
    Shape representing a SVG text
    """
    def __init__(self, name, x, y, text, font_family, font_size, horizontal_align='middle', vertical_align='middle'):
        """
        :param name: name of the SVG shape of the path, used to define the id of the SVG tag.
        :param x: abscissa of the text. Note that the topleft corner/center of the text depends on the alignment.
        :param y: ordinate of the text. Note that the topleft corner/center of the text depends on the alignment.
        :param text: Displayed text
        :param font_family: Font name of the text
        :param font_size: Font size of the text
        :param horizontal_align: Horizontal alignment of the text, "start", "middle" or "end" (for left, center and
        right alignment). Each alignment respectively places the left/center/right part on the {@link #x} abscissa of
        the text.
        :param vertical_align: Vertical alignment of the text, "hanging", "middle" or "baseline" (for top, middle and
        bottom alignment). Each alignment respectively places the top/middle/bottom part on the {@link #y} ordinate of
        the text.

        """
        super().__init__(name)
        self._x = x
        self._y = y
        self._text = text
        self._font_family = font_family
        self._font_size = font_size
        self._horizontal_align = horizontal_align
        self._vertical_align = vertical_align
        self.fill_color = (0, 0, 0)

    @property
    def x(self):
        """
        :return: the abscissa of the text
        """
        return self._x

    @x.setter
    def x(self, value):
        """
         Set the abscissa of the text
         :param value : abscissa of the text
        """
        self._x = value

    @property
    def y(self):
        """
        :return: the ordinate of the text
        """
        return self._y

    @y.setter
    def y(self, value):
        """
         Set the ordinate of the text
         :param value : ordinate of the text
        """
        self._y = value

    @property
    def text(self):
        """
        :return:the displayed text
        """
        return self._text

    @text.setter
    def text(self, value):
        """
        Set the displayed text
        :param value: the displayed text
        """
        self._text = value

    @property
    def font_family(self):
        """
        :return: the font name of the text

        """
        return self._font_family

    @font_family.setter
    def font_family(self, value):
        """
        Set the font name of the text
        :param value: the font name of the text
        """
        self._font_family = value

    @property
    def font_size(self):
        """
        :return: the font size of the text

        """
        return self._font_size

    @font_size.setter
    def font_size(self, value):
        """
        Set the font size of the text
        :param value: the font size of the text
        """
        self._font_size = value

    @property
    def horizontal_align(self):
        """
        Return the Horizontal alignment of the text, "start", "middle" or "end".
        Each alignment respectively places the left/center/right part on the {@link #getX()} abscissa of the text.
        :return: the Horizontal alignment of the text
        """
        return self._horizontal_align

    @horizontal_align.setter
    def horizontal_align(self, value):
        """
        Set the Horizontal alignment of the text. The value can be "start", "middle" or "end".
        Each alignment respectively places the left/center/right part on the {@link #getX()} abscissa of the text.
        :param value : The alignment, "start", "middle" or "end"
        """
        self._horizontal_align = value

    def set_horizontal_left_align(self):
        """
        Set the horizontal alignment so that the left part of the text is placed on the {@link #getX()} abcissa.
        """
        self.horizontal_align = 'start'

    def set_horizontal_center_align(self):
        """
        Set the horizontal alignment so that the center part of the text is placed on the {@link #getX()} abcissa.
        """
        self.horizontal_align = 'center'

    def set_horizontal_right_align(self):
        """
        Set the horizontal alignment so that the right part of the text is placed on the {@link #getX()} abcissa.
        """
        self.horizontal_align = 'end'

    @property
    def vertical_align(self):
        """
        Return the Vertical alignment of the text, "hanging", "middle" or "baseline".
         Each alignment respectively places the top/middle/bottom part on the {@link #getY()}  ordinate of the text.
         :return: the Vertical alignment of the text
        """
        return self._vertical_align

    @vertical_align.setter
    def vertical_align(self, value):
        """
        Set the Horizontal alignment of the text. The value can be "hanging", "middle" or "baseline".
        Each alignment respectively places the top/middle/bottom part on the {@link #getY()}  ordinate of the text.
        :param value : The alignment, "hanging", "middle" or "baseline"
        """
        self._vertical_align = value

    def set_vertical_top_align(self):
        """
        Set the vertical alignment so that the top part of the text is placed on the {@link #getY()} ordinate.
        """
        self.vertical_align = 'hanging'

    def set_vertical_center_align(self):
        """
        Set the vertical alignment so that the middle part of the text is placed on the {@link #getY()} ordinate.
        """
        self.vertical_align = 'middle'

    def set_vertical_bottom_align(self):
        """
        Set the vertical alignment so that the bottom part of the text is placed on the {@link #getY()} ordinate.
        """
        self.vertical_align = 'baseline'

    def save_state(self, turn):
        super().save_state(turn)
        self._save_text(turn)
        self._save_point(turn)
        self._save_font(turn)
        self._save_align(turn)

    def load_state(self, turn):
        super().load_state(turn)
        self._load_text(turn)
        self._load_point(turn)
        self._load_font(turn)
        self._load_align(turn)

    def _save_text(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the displayed text of the text
        :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'text', self.text)

    def _load_text(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the displayed text of the text
        :param turn : turn during which the keyframe occurs
        """
        text = str(self._get_key_frame(turn, 'text'))
        if text is not None:
            self.text = text

    def _save_point(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the coordinates of the text
         :param turn : turn during which the keyframe occurs

        """
        self._add_key_frame(turn, 'x', self.x)
        self._add_key_frame(turn, 'y', self.y)

    def _load_point(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the coordinates of the text
         :param turn : turn during which the keyframe occurs

        """
        x = int(self._get_key_frame(turn, 'x'))
        if x is not None:
            self.x = x
        y = int(self._get_key_frame(turn, 'y'))
        if y is not None:
            self.y = y

    def _save_font(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the font of the text
         :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'fontFamily', '"' + self.font_family + '"')
        self._add_key_frame(turn, 'fontSize', self.font_size)

    def _load_font(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the font of the text
         :param turn : turn during which the keyframe occurs
        """
        ff = str(self._get_key_frame(turn, 'fontFamily'))
        if ff is not None:
            self.font_family = ff
        fs = int(self._get_key_frame(turn, 'fontSize'))
        if fs is not None:
            self.font_size = fs

    def _save_align(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the alignment of the text
         :param turn : turn during which the keyframe occurs

        """
        self._add_key_frame(turn, 'textAnchor', self.horizontal_align)
        self._add_key_frame(turn, 'dominantBaseline', self.vertical_align)

    def _load_align(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the alignment of the text
         :param turn : turn during which the keyframe occurs
        """
        ta = str(self._get_key_frame(turn, 'textAnchor'))
        if ta is not None:
            self.horizontal_align = ta
        db = str(self._get_key_frame(turn, 'dominantBaseline'))
        if db is not None:
            self.vertical_align = db

    def tag_svg(self):
        return 'text'

    def attributes_svg(self):
        return "x=\"%d\" y=\"%d\" dominant-baseline=\"%s\" text-anchor=\"%s\" font-family=\"%s\" font-size=\"%d\"" % (
            self.x,
            self.y,
            self.vertical_align,
            self.horizontal_align,
            self.font_family,
            self.font_size
        )

    def get_content(self):
        return self.text


class Path(Shape):
    """
    Shape representing a SVG path
    """

    class PathElement:
        """
        Contains the information of a specific path element
        """

        # Types of path elements
        MOVE = 0
        LINE = 1
        HORIZONTAL = 2
        VERTICAL = 3
        CLOSE = 4
        CURVE = 5
        SHORT_CURVE = 6
        QUADRATIC = 7
        SHORT_QUADRATIC = 8
        ARC = 9

        # Corresponding letter of the category in the SVG object
        # As each category is an integer, to access to the letter, use CATEGORY_TO_LETTER[category]
        CATEGORY_TO_LETTER = 'MLHVZCSQTA'

        def __init__(self, category, absolute, parameters):
            """
            :param category: Type of the path element, one of the constants of the class
            :param absolute: True if the movement use absolute coordinates, False if it uses relative coordinates
            :param parameters: Parameters of the path element, usually coordinates of the destination. Depends on the
            type of the path element
            """
            self._category = category
            self._absolute = absolute
            self._parameters = parameters

        def __str__(self):
            s = Path.PathElement.CATEGORY_TO_LETTER[self._category]

            # Relative coordinates are encoded with lowercase letters
            if not self._absolute:
                s = s.lower()

            if self._category != Path.PathElement.CLOSE:
                s += ' '
            s += ' '.join(str(x) for x in self._parameters)
            return s

        def __getitem__(self, index):
            """
            :param index:
            :return: the index-th parameter
            """
            return self._parameters[index]

        def __setitem__(self, index, value):
            """
            Replace the index-th parameter by value
            """
            self._parameters[index] = value

    def __init__(self, name, x, y):
        """
        Build a new path
        :param name: name of the SVG shape of the path, used to define the id of the SVG tag.
        :param x: x-coordinate of the first point of the path
        :param y: y-coordinate of the first point of the path
        """
        super().__init__(name)

        # List of elements of the path, describing the different parts of the path.
        self._elements = []

        self.add_move_element(True, x, y)

    def __getitem__(self, item):
        """
        :param item: index, between 1 and the number of elements of the path minus 1
         :return: the index-th element of the path
        """
        return self._elements[item]

    def remove(self, index):
        """
        Remove the index-th element of the path
         :param index : index, between 1 and the number of elements of the path minus 1
        """
        if index < 1 or index >= len(self._elements):
            del self._elements[index]

    @property
    def x(self):
        """
        :return: the abcissa of the first point of the path
        """
        return self[0][0]

    @x.setter
    def x(self, value):
        """
        Set the abcissa of the first point of the path
         :param value : abcissa
        """
        self[0][0] = value

    @property
    def y(self):
        """
        :return: the ordinate of the first point of the path
        """
        return self[0][1]

    @y.setter
    def y(self, value):
        """
        Set the ordinate of the first point of the path
         :param value : ordinate
        """
        self[0][1] = value

    def add_move_element(self, absolute, x, y):
        """
        Add a move element with absolute or relative positioning (the "M" and "m" commands) depending on the boolean
        absolute. From the current point the cursor move to the target point described by x and y.
        :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
        by a vector (x, y).
        :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
        otherwise
        :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
        otherwise
        """
        self._elements.append(Path.PathElement(Path.PathElement.MOVE, absolute, [x, y]))

    def add_line_element(self, absolute, x, y):
        """
         Add a line element with absolute or relative positioning (the "L" and "l" commands) depending on the boolean
         absolute. From the current point the cursor draw a line to the target point described by x and y.
         :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
         by a vector (x, y).
         :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
         otherwise
         :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
         otherwise
        """
        self._elements.append(Path.PathElement(Path.PathElement.LINE, absolute, [x, y]))

    def add_horizontal_line_element(self, absolute, x):
        """
         Add a horizontal line element with absolute or relative positioning (the "H" and "h" commands) depending on the
         boolean absolute. From the current point the cursor draw a line to the target point described by x.
         :param absolute : if true, the x-coordinate of the target point is x, otherwise the target point moved from
         the current point by a vector (x, 0).
         :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
         otherwise
        """
        self._elements.append(Path.PathElement(Path.PathElement.HORIZONTAL, absolute, [x]))

    def add_vertical_line_element(self, absolute, y):
        """
         Add a vertical line element with absolute or relative positioning (the "V" and "v" commands) depending on the
         boolean absolute. From the current point the cursor draw a line to the target point described by y.
         :param absolute : if true, the y-coordinate of the target point is y, otherwise the target point moved from
         the current point by a vector (0, y).
         :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
         otherwise
        """
        self._elements.append(Path.PathElement(Path.PathElement.VERTICAL, absolute, [y]))

    def add_close_element(self):
        """
         Add a close element (the "Z" command). Add a straight line to last moved point (with the command "M" or "m")
         and to the first point of the path if no such point exists.
        """
        self._elements.append(Path.PathElement(Path.PathElement.CLOSE, True, []))

    def add_bezier_curve_element(self, absolute, x1, y1, x2, y2, x, y):
        """
         Add a bezier curve element with absolute or relative positioning (the "C" and "c" commands) depending on the
         boolean absolute. From the current point the cursor draw a bezier to the target point described by x and y
         using the control points described by x1, y1, x2 and y2.
         :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
         by a vector (x, y).
         :param x1 : x coordinate of the first control point if absolute is true, or x-displacement from the current
         point to that point otherwise
         :param y1 : y coordinate of the first control point if absolute is true, or y-displacement from the current
         point to that point otherwise
         :param x2 : x coordinate of the second control point if absolute is true, or x-displacement from the current
         point to that point otherwise
         :param y2 : y coordinate of the second control point if absolute is true, or y-displacement from the current
         point to that point otherwise
         :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
         otherwise
         :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
         otherwise
        """
        self._elements.append(Path.PathElement(Path.PathElement.CURVE, absolute, [x1, y1, x2, y2, x, y]))

    def add_short_bezier_curve_element(self, absolute, x2, y2, x, y):
        """
         Add a shorthanded bezier curve element with absolute or relative positioning (the "S" and "s" commands)
         depending on the boolean absolute.
         
         From the current point the cursor draw a bezier to the target point described by x and y
         using two control points : the second one is described by x2 and y2.
         If this element follows an element added with {@link #addShortBezierCurveElement(boolean, int, int, int, int)}
         or {@link #addBezierCurveElement(boolean, int, int, int, int, int, int)}, or set with
         {@link #setShortBezierCurveElement(int, boolean, int, int, int, int)}. or
         {@link #setBezierCurveElement(int, boolean, int, int, int, int, int, int)}, the first control point is
         symmetrical reflexion of
         the last control point of the previous element. Otherwise the control point is set to the current point.
         :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
         by a vector (x, y).
         :param x2 : x coordinate of the second control point if absolute is true, or x-displacement from the current
         point to that point otherwise
         :param y2 : y coordinate of the second control point if absolute is true, or y-displacement from the current
         point to that point otherwise
         :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
         otherwise
         :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
         otherwise
        """
        self._elements.append(Path.PathElement(Path.PathElement.SHORT_CURVE, absolute, [x2, y2, x, y]))

    def add_quadratic_bezier_curve_element(self, absolute, x1, y1, x, y):
        """
         Add a quadratic bezier curve element with absolute or relative positioning (the "Q" and "q" commands)
         depending on the boolean
         absolute. From the current point the cursor draw a quadratic bezier to the target point described by x and y
         using the control point described by x1, y1.
         :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
         by a vector (x, y).
         :param x1 : x coordinate of the control point if absolute is true, or x-displacement from the current point
         to that point otherwise
         :param y1 : y coordinate of the control point if absolute is true, or y-displacement from the current point
         to that point otherwise
         :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
         otherwise
         :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
         otherwise
        """
        self._elements.append(Path.PathElement(Path.PathElement.QUADRATIC, absolute, [x1, y1, x, y]))

    def add_short_quadratic_bezier_curve_element(self, absolute, x, y):
        """
         Add a shorthanded quadratic bezier curve element with absolute or relative positioning (the "T" and "t"
         commands) depending on the boolean absolute.
         
         From the current point the cursor draw a bezier to the target point described by x and y
         using one control point.
         If this element follows an element added with {@link #addShortQuadraticBezierCurveElement(boolean, int, int)}
         or {@link #addQuadraticBezierCurveElement(boolean, int, int, int, int)}, or set with
         {@link #setShortQuadraticBezierCurveElement(int, boolean, int, int)}.
         or {@link #setQuadraticBezierCurveElement(int, boolean, int, int, int, int)}, the control point is the
         symmetrical reflexion of the control point of the previous element. Otherwise the control point is set to the
         current point.
         :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
         by a vector (x, y).
         :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
         otherwise
         :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
         otherwise
        """
        self._elements.append(Path.PathElement(Path.PathElement.SHORT_QUADRATIC, absolute, [x, y]))

    def add_arc_element(self, absolute, rx, ry, x_axis_rotation, large_arc_flag, sweep_flag, x, y):
        """
         Add an arc element with absolute or relative positioning (the "A" and "a" commands)
         depending on the boolean absolute. From the current point the cursor draw an arc
         to the target point described by x and y following an ellipse described by the given parameters.
         
         :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
         by a vector (x, y).
         :param rx : x-radius of the ellipse
         :param ry : x-radius of the ellipse
         :param x_axis_rotation : rotation of the axes relative an horizontal line
         :param large_arc_flag : for each ellipse joining the current and target points, there are two paths that can be
         followed: the shortest and the longest. If true, the longest is chosen. Otherwise the shortest.
         :param sweep_flag : between two points, two ellipses satisfying the radius and rotation constraints can join
         the current and target points. If true, choose the ellipse such that the angle between the current point and
         the ellipse is positive. Otherwise choose the other ellipse.
         :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
         otherwise
         :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
         otherwise
        """
        if type(large_arc_flag) is bool:
            large_arc_flag = 1 if large_arc_flag else 0
        if type(sweep_flag) is bool:
            sweep_flag = 1 if sweep_flag else 0
        self._elements.append(Path.PathElement(Path.PathElement.ARC, absolute, [rx, ry, x_axis_rotation,
                                                                                large_arc_flag, sweep_flag, x, y]))

    def set_move_element(self, index, absolute, x, y):
        """
        Replace the index-th element by a move element with absolute or relative positioning (the "M" and "m" commands)
        depending on the boolean
        absolute. From the current point the cursor move to the target point described by x and y.
        :param index : an integer from 1 to the number of elements
        :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
        by a vector (x, y)
        :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
        otherwise
        :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
        otherwise
        """
        if index < 1 or index >= len(self._elements):
            return
        self._elements[index] = Path.PathElement(Path.PathElement.MOVE, absolute, [x, y])
        
    def set_line_element(self, index, absolute, x, y):
        """
        Replace the index-th element by a line element with absolute or relative positioning (the "L" and "l" commands)
        depending on the boolean absolute. From the current point the cursor draw a line to the target point described
        by x and y.
        :param index : an integer from 1 to the number of elements
        :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
        by a vector (x, y).
        :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
        otherwise
        :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
        otherwise
        """
        if index < 1 or index >= len(self._elements):
            return
        self._elements[index] = Path.PathElement(Path.PathElement.LINE, absolute, [x, y])
    
    def set_horizontal_line_element(self, index, absolute, x):
        """
        Replace the index-th element by a horizontal line element with absolute or relative positioning
        (the "H" and "h" commands) depending on the boolean
        absolute. From the current point the cursor draw a line to the target point described by x.
        :param index : an integer from 1 to the number of elements
        :param absolute : if true, the x-coordinate of the target point is x, otherwise the target point moved from the
        current point by a vector (x, 0).
        :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
        otherwise
        """
        if index < 1 or index >= len(self._elements):
            return
        self._elements[index] = Path.PathElement(Path.PathElement.HORIZONTAL, absolute, [x])

    def set_vertical_line_element(self, index, absolute, y):
        """
        Replace the index-th element by a vertical line element with absolute or relative positioning
        (the "V" and "v" commands) depending on the boolean
        absolute. From the current point the cursor draw a line to the target point described by y.
        :param index : an integer from 1 to the number of elements
        :param absolute : if true, the y-coordinate of the target point is y, otherwise the target point moved from the
        current point by a vector (0, y).
        :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
        otherwise
        """
        if index < 1 or index >= len(self._elements):
            return
        self._elements[index] = Path.PathElement(Path.PathElement.VERTICAL, absolute, [y])

    def set_close_element(self, index):
        """
        Replace the index-th element by a close element (the "Z" command). Add a straight line to last moved point (
        with the command "M" or "m") and to the first point of the path if no such point exists.
        :param index : an integer from 1 to the number of elements
        """
        if index < 1 or index >= len(self._elements):
            return
        self._elements[index] = Path.PathElement(Path.PathElement.CLOSE, True, [])
  
    def set_bezier_curve_element(self, index, absolute, x1, y1, x2, y2, x, y):
        """
        Replace the index-th element by a bezier curve element with absolute or relative positioning (the "C" and "c"
        commands) depending on the boolean absolute. From the current point the cursor draw a bezier to the target
        point described by x and y using the control points described by x1, y1, x2 and y2.
        :param index : an integer from 1 to the number of elements
        :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
        by a vector (x, y).
        :param x1 : x coordinate of the first control point if absolute is true, or x-displacement from the current
        point to that point otherwise
        :param y1 : y coordinate of the first control point if absolute is true, or y-displacement from the current
        point to that point otherwise
        :param x2 : x coordinate of the second control point if absolute is true, or x-displacement from the current
        point to that point otherwise
        :param y2 : y coordinate of the second control point if absolute is true, or y-displacement from the current
        point to that point otherwise
        :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
        otherwise
        :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
        otherwise
        """
        if index < 1 or index >= len(self._elements):
            return
        self._elements[index] = Path.PathElement(Path.PathElement.CURVE, absolute, [x1, y1, x2, y2, x, y])
  
    def set_short_bezier_curve_element(self, index, absolute, x2, y2, x, y):
        """
        Replace the index-th element by a shorthanded bezier curve element with absolute or relative positioning (the
        "S" and "s" commands) depending on the boolean absolute.
        
        From the current point the cursor draw a bezier to the target point described by x and y
        using two control points : the second one is described by x2 and y2.
        If this element follows an element added with {@link #addShortBezierCurveElement(boolean, int, int, int, int)}
        or {@link #addBezierCurveElement(boolean, int, int, int, int, int, int)}, or set with
        {@link #setShortBezierCurveElement(int, boolean, int, int, int, int)}.
        or {@link #setBezierCurveElement(int, boolean, int, int, int, int, int, int)}, the first control point is
        symmetrical reflexion of the last control point of the previous element. Otherwise the control point is set to
        the current point.
        :param index : an integer from 1 to the number of elements
        :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
        by a vector (x, y).
        :param x2 : x coordinate of the second control point if absolute is true, or x-displacement from the current
        point to that point otherwise
        :param y2 : y coordinate of the second control point if absolute is true, or y-displacement from the current
        point to that point otherwise
        :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
        otherwise
        :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
        otherwise
        """
        if index < 1 or index >= len(self._elements):
            return
        self._elements[index] = Path.PathElement(Path.PathElement.CURVE, absolute, [x2, y2, x, y])
 
    def set_quadratic_bezier_curve_element(self, index, absolute, x1, y1, x, y):
        """
        Replace the index-th element by a quadratic bezier curve element with absolute or relative positioning (the "Q"
        and "q" commands) depending on the boolean
        absolute. From the current point the cursor draw a quadratic bezier to the target point described by x and y
        using the control point described by x1, y1.
        :param index : an integer from 1 to the number of elements
        :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
        by a vector (x, y).
        :param x1 : x coordinate of the control point if absolute is true, or x-displacement from the current point
        to that point otherwise
        :param y1 : y coordinate of the control point if absolute is true, or y-displacement from the current point
        to that point otherwise
        :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
        otherwise
        :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
        otherwise
        """
        if index < 1 or index >= len(self._elements):
            return
        self._elements[index] = Path.PathElement(Path.PathElement.QUADRATIC, absolute, [x1, y1, x, y])
 
    def set_short_quadratic_bezier_curve_element(self, index, absolute, x, y):
        """
        Replace the index-th element by a shorthanded quadratic bezier curve element with absolute or relative
        positioning (the "T" and "t" commands) depending on the boolean absolute.
        
        From the current point the cursor draw a bezier to the target point described by x and y
        using one control point.
        If this element follows an element added with {@link #addShortQuadraticBezierCurveElement(boolean, int, int)}
        or {@link #addQuadraticBezierCurveElement(boolean, int, int, int, int)}, or set with
        {@link #setShortQuadraticBezierCurveElement(int, boolean, int, int)}.
        or {@link #setQuadraticBezierCurveElement(int, boolean, int, int, int, int)}, the control point is the
        symmetrical reflexion of the control point of the previous element. Otherwise the control point is set to the
        current point.
        :param index : an integer from 1 to the number of elements
        :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
        by a vector (x, y).
        :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
        otherwise
        :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
        otherwise
        """
        if index < 1 or index >= len(self._elements):
            return
        self._elements[index] = Path.PathElement(Path.PathElement.SHORT_QUADRATIC, absolute, [x, y])
 
    def set_arc_element(self, index, absolute, rx, ry, x_axis_rotation, large_arc_flag, sweep_flag, x, y):
        """
        Replace the index-th element by an arc element with absolute or relative positioning (the "A" and "a" commands)
        depending on the boolean absolute. From the current point the cursor draw an arc
        to the target point described by x and y following an ellipse described by the given parameters.
        
        :param index : an integer from 1 to the number of elements
        :param absolute : if true, the target point is (x, y), otherwise the target point moved from the current point
        by a vector (x, y).
        :param rx : x-radius of the ellipse
        :param ry : x-radius of the ellipse
        :param x_axis_rotation : rotation of the axes relative an horizontal line
        :param large_arc_flag : for each ellipse joining the current and target points, there are two paths that can
        be followed: the shortest and the longest. If true, the longest is chosen. Otherwise the shortest.
        :param sweep_flag : between two points, two ellipses satisfying the radius and rotation constraints can join
        the current and target points. If true, choose the ellipse such that the angle between the current point and
        the ellipse is positive. Otherwise choose the other ellipse.
        :param x : x coordinate of the target point if absolute is true, or x-displacement from the current point
        otherwise
        :param y : y coordinate of the target point if absolute is true, or y-displacement from the current point
        otherwise
        """
        if index < 1 or index >= len(self._elements):
            return

        if type(large_arc_flag) is bool:
            large_arc_flag = 1 if large_arc_flag else 0
        if type(sweep_flag) is bool:
            sweep_flag = 1 if sweep_flag else 0

        self._elements[index] = Path.PathElement(Path.PathElement.ARC, absolute, [
            rx, ry, x_axis_rotation, large_arc_flag, sweep_flag, x, y])

    @property
    def description(self):
        """
        :return: the SVG description of the path
        """
        return ' '.join([str(element) for element in self._elements])

    @description.setter
    def description(self, value):
        """
        Set the elements of the path using the given description.
        :param value : SVG description of the path
        """
        self._elements.clear()
        index = 0
        spl = value.split(' ')

        letter_to_element_parameters = {
                'm': (self.add_move_element, 2),
                'l': (self.add_line_element, 2),
                'h': (self.add_horizontal_line_element, 1),
                'v': (self.add_vertical_line_element, 1),
                'z': (self.add_close_element, 0),
                'c': (self.add_bezier_curve_element, 6),
                's': (self.add_short_bezier_curve_element, 4),
                'q': (self.add_quadratic_bezier_curve_element, 4),
                't': (self.add_short_quadratic_bezier_curve_element, 2),
                'a': (self.add_arc_element, 7)
            }

        while index < len(spl):
            c = spl[index]
            absolute = c.isupper()

            function, parameters_len = letter_to_element_parameters[c.lower()]
            parameters = [spl[index + 1 + i] for i in range(parameters_len)]
            function(absolute, *parameters)
            index += parameters_len + 1

    def save_state(self, turn):
        super().save_state(turn)
        self._save_description(turn)

    def load_state(self, turn):
        super().load_state(turn)
        self._load_description(turn)

    def _save_description(self, turn):
        """
        Save the keyframe containing the attributes corresponding to the description of the path
        :param turn : turn during which the keyframe occurs
        """
        self._add_key_frame(turn, 'd', self.description)

    def _load_description(self, turn):
        """
        Load the keyframe containing the attributes corresponding to the description of the path
        :param turn : turn during which the keyframe occurs
        """
        d = str(self._get_key_frame(turn, 'd'))
        if d is not None:
            self.description = d

    def tag_svg(self):
        return 'path'

    def attributes_svg(self):
        return "d=\"%s\"" % self.description
