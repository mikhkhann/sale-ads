from unparse_html_element import unparse_html_element


class Element:
    default_css_class = None
    css_class_context_item = None
    css_extra_class_context_item = None
    close = True

    def __init_subclass__(cls, lib, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.lib = lib
        cls.init_class()

    @classmethod
    def init_class(cls):
        pass

    def __init__(self, *, parent, **context):
        self.parent = parent
        self.context = self.lib.Context(element=self, **context)

    def render(self):
        return unparse_html_element(
            self.tag, self.get_attrs(), self.get_content(), close=self.close
        )

    def get_attrs(self):
        attrs = {}
        classes = self.get_css_classes()
        if classes:
            attrs["class"] = str.join(" ", classes)
        return attrs

    def get_css_classes(self):
        classes = []
        cls = (
            getattr(self.context, self.css_class_context_item)
            if self.css_class_context_item
            else None
        )
        if cls:
            classes.append(cls)
        elif cls is not False:
            if self.default_css_class:
                classes.append(self.default_css_class)
            extra = (
                getattr(self.context, self.css_extra_class_context_item)
                if self.css_extra_class_context_item
                else None
            )
            if extra:
                classes.append(extra)
        return classes

    def get_content(self):
        return None

    def create_child(self, cls, **kwargs):
        return cls(parent=self, **kwargs)
