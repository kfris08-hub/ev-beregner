import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
from reuse_model_photos import reuse

class PhotoReuseTests(unittest.TestCase):
 def setUp(self):
  self.donor={'status':'verified','reviewed':True,'src':'/assets/cars/a.webp','sha256':'same','source':'https://commons.wikimedia.org/wiki/File:a.jpg','author':'Photographer','license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','reviewed_at':'2026-10-24'}
  self.manifest={'models':{'donor':copy.deepcopy(self.donor),'new':{'status':'missing'}}}
  self.model={'slug':'new','brand':'Test','model':'Car GT','model_family':'Test Car','indexable':False}
  self.config={'families':[{'donor':'donor','names':['Test Car']}]}
 def test_same_family_keeps_license_and_original_review_and_noindex(self):
  self.assertEqual(reuse([self.model],self.manifest,self.config),['new']);p=self.manifest['models']['new']
  for k in ('src','sha256','source','author','license','license_url','reviewed_at'):self.assertEqual(p[k],self.donor[k])
  self.assertFalse(self.model['indexable']);self.assertEqual(p['shared_from'],'donor')
 def test_body_style_and_generation_do_not_match_by_substring(self):
  for family in ['Test Car Sportback','Test Car SUV','Test Car 2027']:
   self.model['model_family']=family;self.assertFalse(reuse([self.model],self.manifest,self.config))
 def test_restricted_editorial_photo_is_not_reused(self):
  self.manifest['models']['donor']['usage']='editorial-only';self.assertFalse(reuse([self.model],self.manifest,self.config))
 def test_existing_photo_is_never_overwritten(self):
  self.manifest['models']['new']=copy.deepcopy(self.donor);self.assertFalse(reuse([self.model],self.manifest,self.config))
 def test_repeated_build_is_idempotent(self):
  reuse([self.model],self.manifest,self.config);before=copy.deepcopy(self.manifest);self.assertFalse(reuse([self.model],self.manifest,self.config));self.assertEqual(before,self.manifest)
if __name__=='__main__':unittest.main()
