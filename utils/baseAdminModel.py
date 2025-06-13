
from django.utils.translation import gettext_lazy as _

class BtnDeleteSelected:
    custom_name = "تایید"
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            actions['delete_selected'][1] = _(self.custom_name)  # تغییر متن دکمه
        return actions
    