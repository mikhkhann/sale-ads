from functools import cached_property
from types import MappingProxyType

from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy


class _CategoryQuerySet(models.QuerySet):
    def cache(self):
        """
        Cache categories.

        Returns a mapping of cached categories.
        The values of the mapping are cached categories; the keys are
        their primary keys.
        Example:

        >>> non_cached_category = Category.objects.create(
        ...     name="category"
        ... )
        >>> non_cached_child = Category.objects.create(
        ...     name="child", parent=non_cached_category
        ... )
        >>>
        >>> cache = Category.objects.cache()
        >>> len(cache)
        2
        >>> cached_category = cache[non_cached_category.pk]
        >>> cached_child = cache[non_cached_child.pk]
        >>>
        >>> # No database hitting on access to related categories:
        >>> cached_child.parent is cached_category
        True
        >>> (cached_category_child,) = cached_category.all_children
        >>> cached_category_child is cached_child
        True
        >>>
        >>> # Non-database data is cached too:
        >>> cached_child.lowercased_name
        'child'
        >>> cached_child.name = "spam"
        >>> cached_child.lowercased_name
        'child'
        """
        cache = self.in_bulk()
        for category in cache.values():
            category._cache = cache
            if category.parent_id is not None:
                category.parent = cache[category.parent_id]
        return MappingProxyType(cache)


class Category(models.Model):
    class _cacheable_readonly_property(property):
        def __new__(cls, compute=None, **kwargs):
            if compute is not None:
                return super().__new__(cls)
            return lambda compute: cls(compute, **kwargs)

        def __init__(self, compute, *, freeze=None):
            super().__init__()
            self._compute = compute
            self._freeze = freeze
            self.__doc__ = compute.__doc__

        def __get__(self, instance, owner=None):
            if instance is None:
                return super().__get__(instance, owner)
            if instance._cache is not None:
                return getattr(instance, self._cache_attr_name)
            return self._compute(instance)

        def __set_name__(self, owner, name):
            super().__set_name__(owner, name)
            self._cache_attr_name = f"_cached_{name}"
            compute_cache = self._compute
            if self._freeze:
                compute_cache_before_freezing = compute_cache
                compute_cache = lambda category: self._freeze(
                    compute_cache_before_freezing(category)
                )
            cache = cached_property(compute_cache)
            setattr(owner, self._cache_attr_name, cache)
            cache.__set_name__(owner, self._cache_attr_name)

    # ==========================================================
    # Fields

    name = models.CharField(pgettext_lazy("category field", "name"), max_length=200)
    parent = models.ForeignKey(
        "self",
        models.PROTECT,
        "children",
        blank=True,
        null=True,
        verbose_name=pgettext_lazy("category field", "parent"),
    )
    ultimate = models.BooleanField(
        pgettext_lazy("category field", "ultimate"),
        default=False,
        help_text=_("whether can be used as the category of an ad"),
    )

    # --------------------------------------
    # Primary key

    pk_from_string = staticmethod(int)

    # ==========================================================

    objects = _CategoryQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "parent",
                name="parent_and_case_unified_name_unique_together",
            ),
            models.UniqueConstraint(
                Lower("name"),
                condition=models.Q(parent=None),
                name="unique_case_unified_root_name",
            ),
        ]
        verbose_name = pgettext_lazy("model", "category")
        verbose_name_plural = pgettext_lazy("model plural", "categories")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = None

    def get_absolute_url(self):
        from ads.utils import get_category_ad_list_url

        return get_category_ad_list_url(self.pk)

    def __str__(self):
        return self.full_name

    def name_relative_to(self, ancestor):
        r"""
        Example:

        >>> root = Category(name="root")
        >>> root_child = Category(name="root child", parent=root)
        >>> root_grandchild = Category(
        ...     name="root grandchild", parent=root_child
        ... )
        >>>
        >>> # With category
        >>> root_child.name_relative_to(root)
        'root child'
        >>> root_grandchild.name_relative_to(root)
        'root child\xa0/ root grandchild'
        >>>
        >>> # With None
        >>> root.name_relative_to(None)
        'root'
        >>> root_child.name_relative_to(None)
        'root\xa0/ root child'
        >>>
        >>> # With primary key
        >>> root.save()
        >>> root_child.name_relative_to(root.pk)
        'root child'
        """
        invalid_ancestor = False
        if ancestor is None:
            if self.parent is None:
                return self.name
        elif isinstance(ancestor, Category):
            if self.parent == ancestor:
                return self.name
            if self.parent is None:
                invalid_ancestor = f'the "{ancestor.full_name}" category'
        else:
            if self.parent is None:
                invalid_ancestor = f"the category with the primary key {repr(ancestor)}"
            elif self.parent.pk == ancestor:
                return self.name
        if invalid_ancestor:
            raise ValueError(
                f'Can\'t get the name of the "{self.full_name}" category relative to '
                f"{invalid_ancestor}."
            )
        return self._concatenate_parent_and_child_names(
            self.parent.name_relative_to(ancestor), self.name
        )

    @staticmethod
    def _concatenate_parent_and_child_names(parent_name, child_name):
        return f"{parent_name}{Category._NON_BREAKING_SPACE}/ {child_name}"

    _NON_BREAKING_SPACE = "\xa0"

    @property
    def all_children(self):
        if self._cache is not None:
            return self._cached_all_children
        return self.children.all()

    @cached_property
    def _cached_all_children(self):
        return frozenset(
            category for category in self._cache.values() if category.parent == self
        )

    @_cacheable_readonly_property(freeze=frozenset)
    def descendants(self):
        descendants = set(self.all_children)
        for child in self.all_children:
            descendants.update(child.descendants)
        return descendants

    @_cacheable_readonly_property
    def full_name(self):
        r"""
        Example:

        >>> root = Category(name="root")
        >>> root.full_name
        'root'
        >>>
        >>> root_child = Category(name="root child", parent=root)
        >>> root_child.full_name
        'root\xa0/ root child'
        >>>
        >>> root_grandchild = Category(
        ...     name="root grandchild", parent=root_child
        ... )
        >>> root_grandchild.full_name
        'root\xa0/ root child\xa0/ root grandchild'
        """
        return self.name_relative_to(None)

    @_cacheable_readonly_property
    def lowercased_full_name(self):
        if self.parent is not None:
            return self._concatenate_parent_and_child_names(
                self.parent.lowercased_full_name, self.lowercased_name
            )
        return self.lowercased_name

    @_cacheable_readonly_property
    def lowercased_name(self):
        return self.name.lower()

    @_cacheable_readonly_property(freeze=tuple)
    def sorted_children(self):
        """Child categories sorted case-insensitively by name."""
        return sorted(self.all_children, key=lambda category: category.lowercased_name)
