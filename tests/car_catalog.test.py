"""Meaningful ingestion regressions: variant identity, units, failure safety and discovery."""
import copy, importlib.util, json, unittest
from pathlib import Path
from datetime import date
ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('updater',ROOT/'tools/update_car_catalog.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
CONFIG=json.loads((ROOT/'data/car-sources.json').read_text());CATALOG=json.loads((ROOT/'data/cars.json').read_text());CATALOG['models']=[m for m in CATALOG['models'] if m['origin']=='existing'];TODAY=date(2026,10,25)
class CatalogTests(unittest.TestCase):
 def record(self,**changes):
  result={'source_id':'https://example.dk/model|Base','brand':'Test Motors','family':'Test Motors Nybil','model':'Nybil Base','variant':'Base','values':{'price':200000},'source':{'url':'https://example.dk/model','label':'Test','source_date':'2026-10-25','kind':'licensed-feed'}};result.update(changes);return result
 def test_new_model_has_null_unknowns_and_is_not_indexed(self):
  out,r=up.apply_records(CATALOG,[self.record()],CONFIG,TODAY);m=out['models'][-1]
  self.assertEqual(len(r['new_models']),1);self.assertIsNone(m['consumption']);self.assertIsNone(m['range']);self.assertFalse(m['indexable']);self.assertEqual(m['price'],200000)
 def test_repeated_discovery_is_idempotent_and_url_survives_price_change(self):
  out,_=up.apply_records(CATALOG,[self.record()],CONFIG,TODAY);second,r=up.apply_records(out,[self.record()],CONFIG,TODAY);self.assertEqual(out,second);self.assertFalse(r['new_models'])
  second,_=up.apply_records(out,[self.record(values={'price':210000})],CONFIG,TODAY);self.assertEqual(out['models'][-1]['slug'],second['models'][-1]['slug'])
 def test_missing_source_values_never_zero_or_erase(self):
  out,_=up.apply_records(CATALOG,[self.record()],CONFIG,TODAY);second,_=up.apply_records(out,[self.record(values={'price':None})],CONFIG,TODAY);self.assertEqual(second['models'][-1]['price'],200000)
 def test_price_outlier_preserves_last_known_model(self):
  out,_=up.apply_records(CATALOG,[self.record()],CONFIG,TODAY);second,r=up.apply_records(out,[self.record(values={'price':900000})],CONFIG,TODAY);self.assertEqual(second,out);self.assertEqual(len(r['quarantine']),1)
 def test_unbound_variant_cannot_change_existing_trim(self):
  before=copy.deepcopy(CATALOG);record=self.record(brand='Kia',family='Kia EV3',model='EV3 Long Range GT-Line');after,r=up.apply_records(before,[record],CONFIG,TODAY);self.assertEqual(before,after);self.assertTrue(r['unmatched_existing_variants'])
 def test_withdrawn_names_cannot_reappear(self):
  for brand,model in [('Kia','EV1 Base'),('Kia','Sportage EV Base'),('Volvo','EX50 Base'),('Volvo','EX70 Base')]:
   out,r=up.apply_records(CATALOG,[self.record(brand=brand,model=model,family=brand+' '+model)],CONFIG,TODAY);self.assertEqual(out,CATALOG)
 def test_new_batched_automatically_without_approval(self):
  records=[self.record(source_id='https://example.dk/model|'+str(i),model='Nybil '+str(i),family='Nybil '+str(i)) for i in range(30)]
  out,r=up.apply_records(CATALOG,records,CONFIG,TODAY);self.assertEqual(len(r['new_models']),CONFIG['max_new_per_day'])
  out,r=up.apply_records(out,records,CONFIG,TODAY);self.assertEqual(len(r['new_models']),0)
  from datetime import timedelta
  out,r=up.apply_records(out,records,CONFIG,TODAY+timedelta(days=1));self.assertEqual(len(r['new_models']),15)
 def test_future_and_stale_source_dates_are_rejected(self):
  for d in ['2026-10-26','2020-01-01',None]:
   with self.assertRaises(up.SourceError):up.source_date(d,TODAY)
 def test_prices_bool_infinity_negative_rejected(self):
  for v in [True,float('inf'),-1,0,'200000']:
   with self.assertRaises(up.SourceError):up.number(v,'price')
 def retail(self):
  return {'name':'Alfa Romeo Junior','variants':[{'engineId':1,'trimId':1,'price':224990,'consumption':152,'drivingRange':409}], 'trims':[{'id':1,'name':'Core'}], 'engines':[{'id':1,'name':'EL 156','fuelType':'el','batteryCapacity':54,'specifications':{'batteryMaxPower':'207'}}]}
 def test_retail_wh_per_km_becomes_kwh_per_100_km(self):
  records,bad=up.retail_records(self.retail(),CONFIG['retail_apis'][0],TODAY);self.assertFalse(bad);self.assertEqual(records[0]['values']['consumption'],15.2);self.assertEqual(records[0]['bound_slug'],'alfa-romeo-junior-core');self.assertNotIn('charging',records[0]['values'])
 def test_phev_not_imported_as_bev(self):
  dto=self.retail();dto['engines'][0]['fuelType']='phev'
  with self.assertRaises(up.SourceError):up.retail_records(dto,CONFIG['retail_apis'][0],TODAY)
 def test_changed_units_do_not_divide_kwh_values_again(self):
  dto=self.retail();dto['variants'][0]['consumption']=15.2
  with self.assertRaises(up.SourceError):up.retail_records(dto,CONFIG['retail_apis'][0],TODAY)
 def test_wrong_brand_api_rejected(self):
  dto=self.retail();dto['name']='Other Brand Junior'
  with self.assertRaises(up.SourceError):up.retail_records(dto,CONFIG['retail_apis'][0],TODAY)
 def test_sufficient_technical_data_indexes_new_variant(self):
  record=self.record(values={'price':200000,'consumption':16,'range':420},source={'url':'https://example.dk/api','label':'Test','source_date':'2026-10-25','kind':'retail-api'})
  out,_=up.apply_records(CATALOG,[record],CONFIG,TODAY);self.assertTrue(out['models'][-1]['indexable'])
 def test_similar_variant_and_battery_do_not_bind(self):
  record=self.record(brand='BYD',family='BYD Dolphin Surf',variant='Active (50 kWh)',model='Dolphin Surf Active (50 kWh)')
  self.assertIsNone(up.exact_existing_variant(record,CATALOG['models']))
 def test_plus_model_identity_is_distinct(self):
  self.assertNotEqual(up.normalize('P7'),up.normalize('P7+'))
 def test_legacy_model_cannot_be_deleted_after_catalogue_grows(self):
  altered=copy.deepcopy(CATALOG);altered['models'].pop()
  with self.assertRaises(up.SourceError):up.validate_catalog(altered,CONFIG)
 def test_unsafe_source_markup_rejected_before_rendering(self):
  altered=copy.deepcopy(CATALOG);altered['models'][0]['model']='</script><script>bad</script>'
  with self.assertRaises(up.SourceError):up.validate_catalog(altered,CONFIG)
 def test_catalog_validates_existing_models(self):up.validate_catalog(CATALOG,CONFIG)
if __name__=='__main__':unittest.main()
