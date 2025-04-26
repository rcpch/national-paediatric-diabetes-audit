from django.forms import TextInput
from django.db.models import Q

from project.npda.models import NPDAUser
from django_filters import FilterSet, CharFilter

class NPDAUserFilterSet(FilterSet):

    search = CharFilter(
        method='filter_search',
        widget=TextInput(attrs={
            'placeholder': 'Search by email, first name, or surname',
            'class': 'form-control text-center placeholder-gray-300 focus:bg-rcpch_strong_blue_light_tint2 hover:bg-rcpch_strong_blue_light_tint2 focus:placeholder-gray-500 p-2 m-2 w-full',
        }),
        label='Search users',
    )

    class Meta:
        model = NPDAUser
        fields=[]
    
    def filter_search(self, queryset, name, value):
        if value:
            queryset = queryset.filter(
                Q(pk__icontains=value) |
                Q(email__icontains=value) |
                Q(first_name__icontains=value) |
                Q(surname__icontains=value)
            )
        return queryset