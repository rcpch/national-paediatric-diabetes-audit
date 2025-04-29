---
title: NPDA Platform Administrator Guidance
---

## Opening and closing audit years for submission

New audit years do not appear on the platform automatically. They must be created by a superuser using the Django Admin.

- From the admin screen, click "Audit Period"
- Click "Add Audit Period"
- Select the start and end dates

Submission is not automatically closed after the end date. That is controlled by the `is_open` flag.

To create a new audit year but not have it visible to non-admin users, leave `is_visible` unchecked.
You can then test uploading using the RCPCH test PDU.

Once ready to open for submission, tick `is_visible` and `is_open` and save.

Data can still be entered after the `end_date` whilst the `is_open` flag is on. To close an audit period,
change it to off and save.

Don't remove `is_visible` for closed audit periods. This allows users to view their old data and dashboards without
being able to edit it.