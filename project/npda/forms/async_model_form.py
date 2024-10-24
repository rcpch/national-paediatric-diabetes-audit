from django.forms import ModelForm, ValidationError
from django.forms.utils import ErrorDict

from asgiref.sync import async_to_sync

"""
Opt in to support async form cleaning.

To define an async per field cleaner:
    async def aclean_field_name(self):

You can mix async and sync per field cleaners and all will be run.

To define an async form .clean:
    async def aclean(self):

You can't have both an async and a sync clean method for a given field or the whole form,
the async one will take precendence.

You can call afull_clean() to run them all asynchronously or use the existing Django
API calling .errors, .is_valid to run them synchronously. The class keeps track of
what has been run so regardless of how you call it, they will only run once.

This class mirrors the internals of ModelForm so could break across versions.
That said, many people override the methods we mirror so they're unlikely to change.
However you should unit test anything using this to ensure it works across updates.
"""
class AsyncModelForm(ModelForm):
    # Must be called before anything else that triggers full_clean, otherwise it's a no-op
    #  eg .errors, .is_valid
    async def afull_clean(self):
        if self._errors is not None:
            return
        
        self._errors = ErrorDict()
        if not self.is_bound:  # Stop further processing.
            return
        self.cleaned_data = {}
        # If the form is permitted to be empty, and none of the form data has
        # changed from the initial data, short circuit any validation.
        if self.empty_permitted and not self.has_changed():
            return

        await self._aclean_fields()
        await self._aclean_form()

    async def _aclean_fields(self):
        for name, bf in self._bound_items():
            field = bf.field
            try:
                self.cleaned_data[name] = field._clean_bound_field(bf)

                async_cleaner = getattr(self, f"aclean_{name}", None)
                sync_cleaner = getattr(self, f"clean_{name}", None)

                value = None

                if async_cleaner:
                    value = await async_cleaner()
                elif sync_cleaner:
                    value = sync_cleaner()
                
                if value:
                    self.cleaned_data[name] = value
            except ValidationError as e:
                self.add_error(name, e)
    
    async def _aclean_form(self):
        async_cleaner = getattr(self, "aclean", None)
        sync_cleaner = getattr(self, "clean", None)

        cleaned_data = None
        
        try:
            if async_cleaner:
                cleaned_data = await async_cleaner()
            elif sync_cleaner:
                cleaned_data = sync_cleaner()
        except ValidationError as e:
            self.add_error(None, e)
        else:
            if cleaned_data is not None:
                self.cleaned_data = cleaned_data

    # Wire up to the existing Django internals
    def _clean_fields(self):
        return async_to_sync(self._aclean_fields)()
    
    def _clean_form(self):
        return async_to_sync(self._aclean_form)()
