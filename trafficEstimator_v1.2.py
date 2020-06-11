"""

created by Dimitrios Panourgias
June 2020

Always remember to update:
    1) Location code
    2) Language code
    3) Ad group Max cpc (in MicroAmount)

"""

from googleads import adwords
import pandas as pd
df = pd.DataFrame(columns=['query','match_type','est_daily_clicks','est_ad_pos','est_avg_cpc'])
dict = pd.read_csv('traffEstQueries.csv', header=None)

def main(client, data, seedDict):
  # Initialize appropriate service.
  traffic_estimator_service = client.GetService(
      'TrafficEstimatorService', version='v201809')

  # pass query and match type in appropriate dictionary
  list = []
  for i in range(0, len(dict)):
      temp = {'text': seedDict[0][i], 'matchType': seedDict[1][i]}
      list.append(temp)

  # Construct selector object and retrieve traffic estimates.
  keywords = list

  keyword_estimate_requests = []
  for keyword in keywords:
    keyword_estimate_requests.append({
        'keyword': {
            'xsi_type': 'Keyword',
            'matchType': keyword['matchType'],
            'text': keyword['text']
        }
    })


  # Create ad group estimate requests.
  adgroup_estimate_requests = [{
      'keywordEstimateRequests': keyword_estimate_requests,
      'maxCpc': {
          'xsi_type': 'Money',
          'microAmount': '100000'
      }
  }]

  # Create campaign estimate requests.
  campaign_estimate_requests = [{
      'adGroupEstimateRequests': adgroup_estimate_requests,
      'criteria': [
          {
              'xsi_type': 'Location',
              'id': '2250'  # FR.
          },
          {
              'xsi_type': 'Language',
              'id': '1002'  # French.
          }
      ],
  }]

  # Create the selector.
  selector = {
      'campaignEstimateRequests': campaign_estimate_requests,
  }

  # Optional: Request a list of campaign-level estimates segmented by
  # platform.
  selector['platformEstimateRequested'] = True

  # Get traffic estimates.
  estimates = traffic_estimator_service.get(selector)

  campaign_estimate = estimates['campaignEstimates'][0]

  # Display the keyword estimates.
  it = 0
  if 'adGroupEstimates' in campaign_estimate:
    ad_group_estimate = campaign_estimate['adGroupEstimates'][0]
    if 'keywordEstimates' in ad_group_estimate:
      keyword_estimates = ad_group_estimate['keywordEstimates']
      keyword_template = ('Results for the keyword with text "%s" and match '
                          'type "%s":')

      keyword_estimates_and_requests = zip(keyword_estimates,
                                           keyword_estimate_requests)

      for keyword_tuple in keyword_estimates_and_requests:
        if keyword_tuple[1].get('isNegative', False):
          continue
        keyword = keyword_tuple[1]['keyword']
        keyword_estimate = keyword_tuple[0]
        if it == 0:
            endResult = DisplayEstimate(keyword_template % (keyword['text'], keyword['matchType']),
                        keyword_estimate['min'], keyword_estimate['max'], data, keyword['text'], keyword['matchType'])
            it += 1
        else:
            endResult = DisplayEstimate(keyword_template % (keyword['text'], keyword['matchType']),
                            keyword_estimate['min'], keyword_estimate['max'], endResult, keyword['text'],
                            keyword['matchType'])
            it += 1
  return endResult

def _CalculateMean(min_est, max_est):
  if min_est and max_est:
    return (float(min_est) + float(max_est)) / 2.0
  else:
    return None


def _FormatMean(mean):
  if mean:
    return '%.2f' % mean
  else:
    return 'N/A'


def DisplayEstimate(message, min_estimate, max_estimate, df1, query, matchtype):
  """Displays mean average cpc, position, clicks, and total cost for estimate.

  Args:
    message: str message to display for the given estimate.
    min_estimate: zeep.objects.StatsEstimate containing a minimum estimate from the
      TrafficEstimatorService response.
    max_estimate: zeep.objects.StatsEstimate containing a maximum estimate from the
      TrafficEstimatorService response.
  """
  # Find the mean of the min and max values.
  mean_avg_cpc = (_CalculateMean(min_estimate['averageCpc']['microAmount'],
                                 max_estimate['averageCpc']['microAmount'])
                  if 'averageCpc' in min_estimate
                  and min_estimate['averageCpc'] else None)
  mean_avg_pos = (_CalculateMean(min_estimate['averagePosition'],
                                 max_estimate['averagePosition'])
                  if 'averagePosition' in min_estimate
                  and min_estimate['averagePosition'] else None)
  mean_clicks = _CalculateMean(min_estimate['clicksPerDay'],
                               max_estimate['clicksPerDay'])
  mean_total_cost = _CalculateMean(min_estimate['totalCost']['microAmount'],
                                   max_estimate['totalCost']['microAmount'])
  df_add = pd.DataFrame(columns=['query', 'match_type', 'est_daily_clicks', 'est_ad_pos', 'est_avg_cpc'])
  print(message)
  print('  Estimated average CPC: %s' % _FormatMean(mean_avg_cpc))
  print('  Estimated ad position: %s' % _FormatMean(mean_avg_pos))
  print('  Estimated daily clicks: %s' % _FormatMean(mean_clicks))
  print('  Estimated daily cost: %s' % _FormatMean(mean_total_cost))
    
  try:
    df_add = df_add.append({'query': query,
                    'match_type': matchtype,
                    'est_daily_clicks': round(mean_clicks,0),
                    'est_ad_pos': round(mean_avg_pos,1),
                    'est_avg_cpc': round(mean_avg_cpc/1000000,3)},
                    ignore_index=True)
    df1 = pd.concat([df1, df_add], axis=0, ignore_index=True)
  except:
    df_add = df_add.append({'query': query,
                              'match_type': matchtype,
                              'est_daily_clicks': mean_clicks,
                              'est_ad_pos': mean_avg_pos,
                              'est_avg_cpc': mean_avg_cpc},
                             ignore_index=True)
    df1 = pd.concat([df1, df_add], axis=0, ignore_index=True)
    
  return df1

if __name__ == '__main__':
  # Initialize client object.
  adwords_client = adwords.AdWordsClient.LoadFromStorage()

  x = main(adwords_client, df, dict)
  print(x)
