def test_npda_user_list_view_get_query_set_with_users_cannot_view_user_table_from_different_pdus(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
    live_server,
):
    print(f'!! {live_server}')