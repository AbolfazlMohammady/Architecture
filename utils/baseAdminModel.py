
from django.utils.translation import gettext_lazy as _

class BtnDeleteSelected:
    custom_name = "تایید"
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            action_func, _label, *rest = actions['delete_selected']
            # Build a new tuple with translated custom label instead of mutating
            if rest:
                actions['delete_selected'] = (action_func, _(self.custom_name), *rest)
            else:
                actions['delete_selected'] = (action_func, _(self.custom_name))
        return actions
    


    