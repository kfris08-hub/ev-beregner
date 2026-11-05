from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,importlib.util,unittest
ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('fuel',ROOT/'tools/update_fuel_prices.py');fuel=importlib.util.module_from_spec(spec);spec.loader.exec_module(fuel)
NOW=datetime(2026,11,5,12,tzinfo=timezone.utc)
def station(identifier,petrol=16,diesel=18,stamp=None):
 return {'facility_number':identifier,'last_updated_time':stamp or NOW.isoformat(),'prices':[{'product_name':'Blyfri 95','price':petrol},{'product_name':'Svovlfri Diesel','price':diesel},{'product_name':'Oktan 100','price':29.99}]}
class PumpPricesTests(unittest.TestCase):
 def parse(self,items,**kwargs):return fuel.snapshot({'items':items},now=NOW,min_stations=2,**kwargs)
 def test_real_station_prices_are_averaged_once_not_premium_or_list_prices(self):
  a,b=station(1,16,18),station(2,16.2,18.4);result=self.parse([a,b,copy.deepcopy(a)])
  self.assertEqual(result['petrol95'],16.1);self.assertEqual(result['diesel'],18.2);self.assertEqual(result['coverage'],{'petrol95':2,'diesel':2})
  self.assertEqual(result['price_type'],'pump_average');self.assertEqual(result['source_chain'],'OK')
 def test_old_future_and_invalid_timestamps_do_not_become_current(self):
  items=[station(1),station(2),station(3,30,30,(NOW-timedelta(days=4)).isoformat()),station(4,30,30,(NOW+timedelta(days=1)).isoformat()),station(5,30,30,'missing')]
  r=self.parse(items);self.assertEqual(r['petrol95'],16);self.assertEqual(r['excluded_stations'],3)
 def test_timezone_and_check_date_are_separate_from_price_change(self):
  r=self.parse([station(1,stamp='2026-11-05T12:00:00+01:00'),station(2)])
  self.assertEqual(r['oldest_station_update'],'2026-11-05T11:00:00+00:00');self.assertEqual(r['updated'],NOW.isoformat(timespec='seconds'))
 def test_missing_products_do_not_borrow_premium_prices(self):
  a=station(1);a['prices']=[{'product_name':'Oktan 100','price':29.99}]
  with self.assertRaises(fuel.FuelDataError):self.parse([a,station(2)])
 def test_unknown_currency_units_zero_nan_and_boolean_prices_rejected(self):
  for value in [0,1609,-1,True,float('nan'),'16 kr/l']:
   with self.subTest(value=value),self.assertRaises(fuel.FuelDataError):self.parse([station(1,petrol=value),station(2)])
 def test_conflicting_duplicate_station_and_product_rejected(self):
  with self.assertRaises(fuel.FuelDataError):self.parse([station(1),station(1,17,19),station(2)])
  a=station(1);a['prices'].append({'product_name':'Blyfri 95','price':17})
  with self.assertRaises(fuel.FuelDataError):self.parse([a,station(2)])
 def test_partial_api_response_cannot_quietly_replace_wide_coverage(self):
  previous={'price_type':'pump_average','coverage':{'petrol95':4,'diesel':4}}
  with self.assertRaises(fuel.FuelDataError):self.parse([station(1),station(2)],previous=previous)
 def test_invalid_schema_and_empty_data_fail_closed(self):
  for payload in [None,{},[],{'items':[]},{'items':[{}]}]:
   with self.subTest(payload=payload),self.assertRaises(fuel.FuelDataError):fuel.snapshot(payload,now=NOW,min_stations=2)
if __name__=='__main__':unittest.main()
