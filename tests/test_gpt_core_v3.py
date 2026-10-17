"""Protect meaning of new categorical shares and their forecast timing."""
import sys
import unittest
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from sentiment_project.common import digest
from analyze_gpt_core_v3 import enrich

class ContentFeatureTests(unittest.TestCase):
    def make(self,n,source,tone,price='neither',style='factual',political='none',discovered=None):
        i={'id':str(n),'source':source,'platform':'news','text':'US economic text',
           'published_at':'2020-01-15T12:00:00Z'}
        if discovered:i['discovered_at']=discovered
        lab={'tone':tone,'us_relevance':'yes','topics':['prices'],'price_frame':price,
             'language_style':style,'political_attribution':political,'scope_frame':'national'}
        return i,{'id':i['id'],'input_sha256':digest(i),'label':lab}
    def test_outlet_weight_and_uncertain_denominators(self):
        pairs=[self.make(1,'a','negative','levels'),self.make(2,'a','uncertain','levels'),
               self.make(3,'b','positive')]
        f=enrich([p[0] for p in pairs],[p[1] for p in pairs]).set_index('media_month')
        row=f.loc['2020-01']
        self.assertEqual(row.news_tone,0)
        self.assertEqual(row.news_scored_n,2)
        self.assertEqual(row.news_eligible_n,3)
        self.assertEqual(row.news_price_levels_share,.5)
        self.assertTrue(pd.isna(f.loc['2020-02'].news_price_levels_share))
    def test_late_discovery_excluded_from_frames_too(self):
        i,r=self.make(1,'a','negative','levels',discovered='2020-02-01T00:00:00Z')
        row=enrich([i],[r]).set_index('media_month').loc['2020-01']
        self.assertEqual(row.news_eligible_n,0)
        self.assertTrue(pd.isna(row.news_price_levels_share))
    def test_political_and_emotional_frames_are_independent_of_tone(self):
        i,r=self.make(1,'a','positive','changes','emotional','credit')
        row=enrich([i],[r]).set_index('media_month').loc['2020-01']
        self.assertEqual(row.news_tone,1)
        self.assertEqual(row.news_emotional_share,1)
        self.assertEqual(row.news_political_blame_share,0)
        self.assertEqual(row.news_price_levels_share,0)

if __name__=='__main__':unittest.main()
