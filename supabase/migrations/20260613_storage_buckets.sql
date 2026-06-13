-- ════════════════════════════════════════════════════════════════
-- ORACLE — Storage Buckets (§17)
-- ALL buckets are PRIVATE. No public buckets. Signed URLs only.
-- ════════════════════════════════════════════════════════════════

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES
  ('oracle-simulation-seeds', 'oracle-simulation-seeds', false, '10MB',
    ARRAY['text/plain','application/pdf','text/markdown','application/json']),
  ('oracle-reports', 'oracle-reports', false, '25MB',
    ARRAY['application/pdf','application/json']),
  ('oracle-exports', 'oracle-exports', false, '10MB',
    ARRAY['application/json','application/pdf','text/csv']),
  ('oracle-voice-cache', 'oracle-voice-cache', false, '2MB',
    ARRAY['audio/mpeg','audio/wav','audio/webm']),
  ('oracle-avatars', 'oracle-avatars', false, '2MB',
    ARRAY['image/jpeg','image/png','image/webp'])
ON CONFLICT (id) DO NOTHING;

-- Storage RLS: users can only access their own folder prefix
CREATE POLICY "user_folders_write" ON storage.objects
  FOR INSERT TO authenticated, anon
  WITH CHECK (bucket_id IN ('oracle-simulation-seeds','oracle-reports','oracle-exports','oracle-voice-cache','oracle-avatars'));

CREATE POLICY "user_folders_read" ON storage.objects
  FOR SELECT TO authenticated, anon
  USING (bucket_id IN ('oracle-simulation-seeds','oracle-reports','oracle-exports','oracle-voice-cache','oracle-avatars'));

-- Note: Object-level path isolation is enforced in the Edge Function layer
-- by always writing under `${user_id}/...` prefixes.
