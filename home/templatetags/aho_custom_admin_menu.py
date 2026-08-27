"""Compatibility override for django-admin-menu.

The upstream tag assumes every viewable model has a registered changelist URL.
That is not true for a few permission-limited AHO admin models and caused the
whole dashboard to fail for standard staff users.
"""

from collections import OrderedDict

from admin_menu.templatetags.custom_admin_menu import (
    PERM,
    get_admin_site,
    get_app_list,
    make_menu_group,
    make_menu_item,
)
from django import template
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _


register = template.Library()


@register.simple_tag(takes_context=True)
def get_admin_menu(context):
    request = context["request"]
    admin_site = get_admin_site(context)
    apps = get_app_list(context, True)

    menu = OrderedDict(
        {
            _("Dashboard"): make_menu_group(
                _("Dashboard"),
                weight=1,
                children=[
                    make_menu_item(
                        reverse("admin:index", current_app=admin_site.name),
                        _("Dashboard"),
                        weight=0,
                    )
                ],
            )
        }
    )

    for app in apps:
        if not app["has_module_perms"]:
            continue

        for model in app["models"]:
            # Some custom ModelAdmin classes expose view permission without a
            # reversible changelist. Upstream indexes admin_url unconditionally.
            admin_url = model.get("admin_url")
            if not model["perms"].get(PERM) or not admin_url:
                continue

            model_admin = model["model_admin"]
            title = capfirst(getattr(model_admin, "menu_group", app["name"]))
            if title not in menu:
                menu[title] = make_menu_group(title)

            group = menu[title]
            group.children.append(
                make_menu_item(
                    url=admin_url,
                    title=capfirst(getattr(model_admin, "menu_title", model["name"])),
                    weight=getattr(model_admin, "menu_order", 10),
                )
            )

            extra = getattr(model_admin, "extra_menu_items", [])
            extra_func = getattr(model_admin, "get_extra_menu_items", None)
            if extra_func:
                extra = extra_func(request)

            for item in extra:
                if len(item) == 2:
                    url, extra_title = item
                    weight = 1
                else:
                    url, extra_title, extra_group, weight = item
                    if extra_group not in menu:
                        menu[extra_group] = make_menu_group(extra_group)
                    group = menu[extra_group]

                group.children.append(
                    make_menu_item(
                        url=url,
                        title=capfirst(extra_title),
                        weight=weight,
                    )
                )

    menu = OrderedDict(sorted(menu.items(), key=lambda item: item[1].weight))
    admin_index = reverse("admin:index", current_app=admin_site.name)

    for title in reversed(list(menu.keys())):
        menu[title].children.sort(key=lambda item: item.weight)
        for index, submenu in enumerate(menu[title].children):
            if index == 0:
                menu[title].url = submenu.url
            if submenu.url == admin_index:
                is_active = request.path == submenu.url
            else:
                is_active = request.path.startswith(submenu.url)
            if is_active:
                submenu.active = True
                menu[title].active = True

    return menu
