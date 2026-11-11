"""Notification and freshness tests must not contact third-party services."""
import io,json,sys,unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import notify_search_engines as n
from check_growth_health import assess
class Response:
 def __init__(self,status):self.status=status
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,*args):return b''
class GrowthTests(unittest.TestCase):
 def test_only_this_canonical_host_is_accepted(self):
  for u in ['http://www.evberegn.dk/','https://other.example/','https://www.evberegn.dk/?state=1','https://www.evberegn.dk/#state=1','https://www.evberegn.dk/../x']:
   self.assertFalse(n.own_url(u))
 def test_sitemap_deduplicates_and_tracks_real_dates_and_images(self):
  body='<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://www.evberegn.dk/</loc><lastmod>2026-11-11</lastmod></url></urlset>'
  snap=n.snapshot(body);self.assertEqual(n.changed(snap,snap),[]);self.assertEqual(n.changed(snap,{}),['https://www.evberegn.dk/'])
  with self.assertRaises(ValueError):n.snapshot(body.replace('</urlset>',body[body.index('<url>'):body.index('</url>')+6]+'</urlset>'))
 def test_deleted_urls_can_be_reported_but_never_foreign_state(self):
  self.assertEqual(n.changed({}, {'https://www.evberegn.dk/old/':{}}),['https://www.evberegn.dk/old/'])
  with self.assertRaises(ValueError):n.changed({}, {'https://evil.example/':{}})
 def test_accepted_is_not_an_indexing_confirmation(self):
  payload={'host':'www.evberegn.dk','urlList':['https://www.evberegn.dk/']}
  def opener(req,timeout):self.assertEqual(req.full_url,n.ENDPOINT);self.assertEqual(req.method,'POST');return Response(202)
  self.assertEqual(n.submit(payload,opener=opener),202)
 def test_502_retries_and_403_does_not_retry(self):
  calls=[]
  def opener(req,timeout):
   calls.append(1)
   if len(calls)==1:raise HTTPError(req.full_url,502,'temp',{},None)
   return Response(200)
  self.assertEqual(n.submit({},opener=opener,pause=lambda _:None),200);self.assertEqual(len(calls),2)
  def forbidden(req,timeout):raise HTTPError(req.full_url,403,'forbidden',{},None)
  with self.assertRaises(RuntimeError):n.submit({},opener=forbidden,pause=lambda _:None)
 def test_rate_limit_is_respected(self):
  waits=[];calls=[]
  def opener(req,timeout):
   calls.append(1)
   if len(calls)==1:raise HTTPError(req.full_url,429,'wait',{'Retry-After':'30'},None)
   return Response(200)
  self.assertEqual(n.submit({},opener=opener,pause=waits.append),200);self.assertEqual(waits,[30])
 def test_fresh_data_passes_and_old_or_future_data_is_visible(self):
  now=datetime(2026,11,11,12,tzinfo=timezone.utc);stamp=now.isoformat()
  fuel={'checked_at':stamp,'price_type':'pump_average'};cars={'checked_at':stamp,'sources':[{'status':'ok'}]}
  self.assertFalse(assess(fuel,cars,now)['errors'])
  for delta in [-49,1]:
   self.assertTrue(assess({**fuel,'checked_at':(now+timedelta(hours=delta)).isoformat()},cars,now)['errors'])
  self.assertTrue(assess(fuel,{**cars,'sources':[{'status':'error'}]},now)['errors'])
  self.assertTrue(assess(fuel,{**cars,'checked_at':(now-timedelta(hours=73)).isoformat()},now)['errors'])
if __name__=='__main__':unittest.main()

