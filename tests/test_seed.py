import unittest,tempfile,shutil,subprocess,sqlite3
from pathlib import Path
class SeedTest(unittest.TestCase):
 def test_second_seed_preserves_existing_rows(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'db').mkdir();shutil.copy('med_seo_db_manager.py',root);shutil.copy('db/schema.sql',root/'db/schema.sql')
   subprocess.run(['python3',str(root/'med_seo_db_manager.py')],check=True,capture_output=True)
   db=sqlite3.connect(root/'db/med_seo_intelligence.sqlite');db.execute("UPDATE medical_content_variants SET procedure_name='PRESERVE' WHERE id=1");db.commit();db.close()
   subprocess.run(['python3',str(root/'med_seo_db_manager.py')],check=True,capture_output=True)
   db=sqlite3.connect(root/'db/med_seo_intelligence.sqlite');self.assertEqual(db.execute('SELECT procedure_name FROM medical_content_variants WHERE id=1').fetchone()[0],'PRESERVE');db.close()
if __name__=='__main__':unittest.main()
