"""Share already reviewed, freely licensed photos only within curated model families."""
import copy,re,unicodedata

def normalized(value):
 value=unicodedata.normalize('NFKD',str(value).replace('ø','o').replace('Ø','O'))
 return re.sub(r'[^a-z0-9]+',' ',value.encode('ascii','ignore').decode().lower()).strip()

def reuse(models,manifest,config):
 families={normalized(name):entry['donor'] for entry in config['families'] for name in entry['names']}
 changed=[]
 for model in models:
  slug=model['slug'];current=manifest['models'].get(slug,{})
  if current.get('status')!='missing':continue
  # Exact curated family identity, never a name substring or fuzzy similarity.
  family=model.get('model_family')
  donor_slug=families.get(normalized(family)) if family else None
  donor=manifest['models'].get(donor_slug,{})
  if donor.get('status')!='verified' or donor.get('reviewed') is not True or donor.get('usage')=='editorial-only':continue
  photo=copy.deepcopy(donor)
  photo.update(label=model['brand']+' '+model['model'],shared_from=donor_slug,matched_family=family,caption='Modelbillede. Udstyr, farve og fælge kan afvige fra den valgte variant.')
  manifest['models'][slug]=photo;changed.append(slug)
 return changed
