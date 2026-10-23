
from types import SimpleNamespace

from authorization import (
    can_delete_document,
    can_edit_document,
    can_manage_sharing,
    can_read_document,
)


def make_user(user_id, role="viewer", is_active=True):
    return SimpleNamespace(id=user_id, role=role, is_active=is_active)


def make_document(owner_id):
    return SimpleNamespace(owner_id=owner_id)


def make_permission(can_read=True, can_edit=False):
    return SimpleNamespace(can_read=can_read, can_edit=can_edit)


def test_owner_can_read_edit_delete_and_share():
    owner = make_user(1, role="owner")
    document = make_document(owner_id=1)

    assert can_read_document(owner, document)
    assert can_edit_document(owner, document)
    assert can_delete_document(owner, document)
    assert can_manage_sharing(owner, document)


def test_ungranted_user_cannot_access_document():
    viewer = make_user(2)
    document = make_document(owner_id=1)

    assert not can_read_document(viewer, document)
    assert not can_edit_document(viewer, document)
    assert not can_delete_document(viewer, document)
    assert not can_manage_sharing(viewer, document)


def test_read_grant_does_not_allow_editing():
    viewer = make_user(2)
    document = make_document(owner_id=1)
    permission = make_permission(can_read=True, can_edit=False)

    assert can_read_document(viewer, document, permission)
    assert not can_edit_document(viewer, document, permission)
    assert not can_delete_document(viewer, document)
    assert not can_manage_sharing(viewer, document)


def test_edit_grant_also_allows_reading():
    editor = make_user(2)
    document = make_document(owner_id=1)
    permission = make_permission(can_read=False, can_edit=True)

    assert can_read_document(editor, document, permission)
    assert can_edit_document(editor, document, permission)


def test_administrator_does_not_automatically_read_documents():
    admin = make_user(3, role="administrator")
    document = make_document(owner_id=1)

    assert not can_read_document(admin, document)
    assert not can_edit_document(admin, document)
    assert not can_delete_document(admin, document)
    assert not can_manage_sharing(admin, document)


def test_inactive_user_cannot_access_document():
    inactive_owner = make_user(1, role="owner", is_active=False)
    document = make_document(owner_id=1)

    assert not can_read_document(inactive_owner, document)
    assert not can_edit_document(inactive_owner, document)
    assert not can_delete_document(inactive_owner, document)
    assert not can_manage_sharing(inactive_owner, document)
