from django.test import RequestFactory, SimpleTestCase
from unittest.mock import patch

from . import views


class DummySession(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modified = False


class LaporanDeleteTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, method, path, data=None, session=None):
        request = getattr(self.factory, method)(path, data=data or {})
        request.session = session or DummySession()
        return request

    def test_list_marks_approved_missing_miles_as_undeletable(self):
        session = DummySession(
            {
                'riwayat_staf': [
                    {
                        'id': 'tx-1',
                        'tipe': 'Transfer',
                        'member_name': 'John W. Doe',
                        'member_email': 'john@example.com',
                        'miles': -5000,
                        'waktu': '2025-01-15 10:30',
                    },
                    {
                        'id': 'tx-2',
                        'tipe': 'Klaim',
                        'member_name': 'Budi A. Santoso',
                        'member_email': 'budi@example.com',
                        'miles': 2500,
                        'waktu': '2025-02-05 11:45',
                        'status': 'Disetujui',
                    },
                ]
            }
        )
        request = self._request('get', '/laporan/', session=session)

        response = views.laporan_list(request)
        content = response.content.decode()

        self.assertIn('Penghapusan riwayat transaksi bersifat permanen', content)
        self.assertIn('Riwayat yang dihapus juga tidak lagi tampil untuk Member.', content)
        self.assertIn('Riwayat Klaim Missing Miles yang sudah Disetujui tidak dapat dihapus.', content)
        self.assertIn('title="Riwayat Klaim Missing Miles yang sudah Disetujui tidak dapat dihapus."', content)

    def test_delete_removes_deletable_transaction(self):
        session = DummySession(
            {
                'riwayat_staf': [
                    {
                        'id': 'tx-1',
                        'tipe': 'Transfer',
                        'member_name': 'John W. Doe',
                        'member_email': 'john@example.com',
                        'miles': -5000,
                        'waktu': '2025-01-15 10:30',
                    },
                    {
                        'id': 'tx-2',
                        'tipe': 'Klaim',
                        'member_name': 'Budi A. Santoso',
                        'member_email': 'budi@example.com',
                        'miles': 2500,
                        'waktu': '2025-02-05 11:45',
                        'status': 'Disetujui',
                    },
                ]
            }
        )
        request = self._request('post', '/laporan/delete/tx-1/', session=session)

        with patch('laporan.views.messages.success') as success, patch('laporan.views.messages.error') as error:
            response = views.laporan_delete(request, 'tx-1')

        self.assertEqual(response.status_code, 302)
        self.assertEqual([item['id'] for item in session['riwayat_staf']], ['tx-2'])
        self.assertTrue(session.modified)
        success.assert_called_once()
        error.assert_not_called()

    def test_delete_blocks_approved_missing_miles_claim(self):
        session = DummySession(
            {
                'riwayat_staf': [
                    {
                        'id': 'tx-1',
                        'tipe': 'Transfer',
                        'member_name': 'John W. Doe',
                        'member_email': 'john@example.com',
                        'miles': -5000,
                        'waktu': '2025-01-15 10:30',
                    },
                    {
                        'id': 'tx-2',
                        'tipe': 'Klaim',
                        'member_name': 'Budi A. Santoso',
                        'member_email': 'budi@example.com',
                        'miles': 2500,
                        'waktu': '2025-02-05 11:45',
                        'status': 'Disetujui',
                    },
                ]
            }
        )
        request = self._request('post', '/laporan/delete/tx-2/', session=session)

        with patch('laporan.views.messages.success') as success, patch('laporan.views.messages.error') as error:
            response = views.laporan_delete(request, 'tx-2')

        self.assertEqual(response.status_code, 302)
        self.assertEqual([item['id'] for item in session['riwayat_staf']], ['tx-1', 'tx-2'])
        self.assertFalse(session.modified)
        error.assert_called_once_with(request, 'Riwayat Klaim Missing Miles yang sudah Disetujui tidak dapat dihapus.')
        success.assert_not_called()
