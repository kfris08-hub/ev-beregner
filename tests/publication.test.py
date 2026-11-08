"""Regressions for the observed 502 and an accepted but delayed Pages build."""
import io,sys,unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import Mock,patch
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import publish_site as p

class PublicationTests(unittest.TestCase):
 def simulate(self,outcomes,matches,max_wait=25):
  now=[0];request=Mock(side_effect=outcomes);check=Mock(side_effect=matches)
  def pause(seconds):now[0]+=seconds
  with redirect_stdout(io.StringIO()):p.publish('data/fuel-prices.json',{'checked_at':'new'},'test/repo','test-token',max_wait=max_wait,request=request,check=check,pause=pause,clock=lambda:now[0])
  return request,check
 def test_502_retries_and_only_accepts_the_published_snapshot(self):
  request,check=self.simulate(['temporary-error','requested'],[False,False,False,True]);self.assertEqual(request.call_count,2);self.assertEqual(check.call_count,4)
 def test_502_that_actually_queued_a_build_does_not_duplicate_it(self):
  request,_=self.simulate(['temporary-error'],[False,True]);self.assertEqual(request.call_count,1)
 def test_409_existing_build_is_waited_for(self):
  request,_=self.simulate(['already-pending'],[False,False,True]);self.assertEqual(request.call_count,1)
 def test_already_public_data_needs_no_new_build(self):
  request,_=self.simulate([],[True]);request.assert_not_called()
 def test_timeout_does_not_report_success(self):
  with self.assertRaises(RuntimeError):self.simulate(['requested'],[False]*20,max_wait=15)
 def test_permission_failure_is_not_hidden_by_retries(self):
  with patch.object(p,'urlopen',side_effect=HTTPError('https://api.github.com/',403,'Forbidden',{},None)):
   with self.assertRaisesRegex(RuntimeError,'403'):p.request_build('test/repo','test-token')
 def test_transient_http_error_can_be_retried(self):
  with patch.object(p,'urlopen',side_effect=HTTPError('https://api.github.com/',502,'Bad Gateway',{},None)):self.assertEqual(p.request_build('test/repo','test-token'),'temporary-error')
if __name__=='__main__':unittest.main()
