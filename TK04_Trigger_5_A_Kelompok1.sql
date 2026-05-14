-- TK04 Trigger dan Stored Procedure
-- Ganti [Kelas] dan [Nama_Kelompok] dengan yang sesuai

SET search_path TO AEROMILES;

-- 1. Trigger: Sinkronisasi Total Miles setelah Klaim Disetujui
CREATE OR REPLACE FUNCTION update_miles_on_claim_approved()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status_penerimaan = 'Disetujui' AND OLD.status_penerimaan <> 'Disetujui' THEN
        -- Tambah 1000 miles ke award_miles dan total_miles member
        UPDATE aeromiles.MEMBER
        SET award_miles = award_miles + 1000,
            total_miles = total_miles + 1000
        WHERE email = NEW.email_member;

        -- Pesan sukses wajib
        RAISE NOTICE 'SUKSES: Total miles Member "%" telah diperbarui. Miles ditambahkan: 1000 miles dari klaim penerbangan "%".', NEW.email_member, NEW.flight_number;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_claim_approved ON aeromiles.CLAIM_MISSING_MILES;

CREATE TRIGGER trigger_claim_approved
AFTER UPDATE ON aeromiles.CLAIM_MISSING_MILES
FOR EACH ROW
EXECUTE FUNCTION update_miles_on_claim_approved();


-- 2. Stored Procedure / Function: Pemeringkatan Top 5 Member
-- Karena PostgreSQL FUNCTION bisa return table, kita gunakan FUNCTION RETURNS TABLE
CREATE OR REPLACE FUNCTION get_top_5_member()
RETURNS TABLE (
    email VARCHAR,
    total_miles INTEGER,
    pesan TEXT
) AS $$
DECLARE
    top1_email VARCHAR;
    top1_miles INTEGER;
    dinamis_pesan TEXT;
BEGIN
    -- Ambil peringkat pertama untuk pesan
    SELECT m.email, m.total_miles INTO top1_email, top1_miles
    FROM aeromiles.MEMBER m
    ORDER BY m.total_miles DESC
    LIMIT 1;

    dinamis_pesan := 'SUKSES: Daftar Top 5 Member berdasarkan total miles berhasil diperbarui, dengan peringkat pertama "' || top1_email || '" memiliki ' || top1_miles || ' miles.';

    RAISE NOTICE '%', dinamis_pesan;

    RETURN QUERY
    SELECT m.email, m.total_miles, dinamis_pesan
    FROM aeromiles.MEMBER m
    ORDER BY m.total_miles DESC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;
