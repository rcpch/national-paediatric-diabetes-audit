from django.urls import reverse


def data_breadcrumbs(pdu, audit_period, entries):
    return [
        {
            "label": label,
            "href": reverse(viewname, kwargs={
                "pz_code": pdu.pz_code,
                "audit_period": audit_period.slug
            })
        } for (label, viewname) in entries
    ]