import React from 'react';
import { runRequest } from '@eeacms/search';
import { PieChart } from './PieChart';
import { BarChart } from './BarChart';
import { Grid, Table } from 'semantic-ui-react'; // , Segment

// const getPercentage = (value, total) => {
//   return (value * 100) / total;
// };

const REQUEST = {
  size: 0,
  aggs: {
    Descriptors: {
      terms: {
        field: 'Descriptors',
      },
    },
    Sectors: {
      terms: {
        field: 'Sector',
      },
    },
    MeasureImpacts: {
      terms: {
        field: 'Measure Impacts to',
      },
    },
    Origin: {
      terms: {
        field: 'Origin of the measure',
      },
    },
    OriginByDescriptor: {
      terms: {
        field: 'Descriptors',
      },
      aggs: {
        Origin: {
          terms: {
            field: 'Origin of the measure',
          },
        },
      },
    },
  },
};

const getMeasureImpacts = (data) => {
  const rawData = data.MeasureImpacts.buckets.map(({ key, doc_count }) => ({
    id: key,
    label: key,
    value: doc_count,
  }));
  const total = rawData.reduce((acc, n) => acc + n.value, 0);
  return rawData.map((v) => ({ ...v, value: v.value / total }));
};

const getOriginOfMeasure = (data) => {
  const rawData = data.Origin.buckets.map(({ key, doc_count }) => ({
    id: key,
    label: key,
    value: doc_count,
  }));
  const total = rawData.reduce((acc, n) => acc + n.value, 0);
  return rawData.map((v) => ({ ...v, value: v.value / total }));
};

const getSectors = (data) => {
  const rawData = data.Sectors.buckets.map(({ key, doc_count }) => ({
    id: key,
    label: key,
    value: doc_count,
  }));
  // console.log('sector data', { rawData, data });
  const total = rawData.reduce((acc, n) => acc + n.value, 0);
  return rawData.map((v) => ({ ...v, value: v.value / total }));
};

/**
 * Prepare data for bar chart. Data is an array of objects like:
 *
 * {
 *  BD (Directive 79/409/EEC): 2260
 *  Descriptor: "D1"
 *  HD (Directive 92/43/EEC): 1865
 *  MSFD (Directive 2008/56/EC): 78
 *  Sectorial: 8
 *  WFD (Directive 2000/60/EC): 12
 * }
 */
const getBarChartData = (data, originKeys) => {
  const allOrigins = data ? data.Origin.buckets.map(({ key }) => key) : [];
  const fallback = Object.assign(
    {},
    ...allOrigins.map((Origin) => ({ [Origin]: 0 })),
  );

  const res = data.OriginByDescriptor.buckets.map(
    ({ key, doc_count, Origin }) => ({
      Descriptor: key,
      ...fallback,
      ...Object.assign(
        {},
        ...Origin.buckets.map(({ key, doc_count }) => ({ [key]: doc_count })),
      ),
    }),
  );

  return res;
};

const OriginTable = ({ columns, rows, data }) => {
  return (
    <Table>
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell>Origin of measure</Table.HeaderCell>
          {columns.map((col) => (
            <Table.HeaderCell key={col}>{col}</Table.HeaderCell>
          ))}
        </Table.Row>
        {rows.map((origin) => (
          <Table.Row key={origin}>
            <Table.HeaderCell>{origin}</Table.HeaderCell>
            {columns.map((descriptor, i) => (
              <Table.Cell key={`${i}-${descriptor}`}>
                {data[i][origin]}
              </Table.Cell>
            ))}
          </Table.Row>
        ))}
        <Table.Row>
          <Table.HeaderCell>Total</Table.HeaderCell>
          {data.map((item) => (
            <Table.Cell key={item.Descriptor}>
              {rows
                .map((r) => parseInt(item[r]) || 0)
                .reduce((a, b) => a + b, 0)}
            </Table.Cell>
          ))}
        </Table.Row>
      </Table.Header>
    </Table>
  );
};

const ChartsIntro = (props) => {
  const { appConfig } = props;
  const [chartData, setChartData] = React.useState();
  const [outsideText, setOutsideText] = React.useState('');

  React.useEffect(() => {
    let alreadyRequested = false;

    async function fetchData() {
      const resp = await runRequest(REQUEST, appConfig);
      if (!alreadyRequested) setChartData(resp.body?.aggregations);
    }
    fetchData();
    return () => {
      alreadyRequested = true;
    };
  }, [appConfig]);

  const targetNode = React.useRef();

  React.useEffect(() => {
    const originNode = document.querySelector('#has_context_text');
    if (originNode) {
      const url = new URL(window.location);
      url.search = '';
      fetch(url.toString(), {
        headers: {
          Accept: 'application/json',
        },
      })
        .catch((error) => {
          // eslint-disable-next-line
          console.log('Error in making backend server request', error);
        })
        .then((response) => response.json())
        .catch((error) => {
          // eslint-disable-next-line
          console.log('Error in reading intro text from backend server', error);
        })
        .then((data) => setOutsideText(data?.text?.data));
    }
  }, []);

  // const allOrigins = chartData
  //   ? chartData.Origin.buckets.map(({ key }) => key)
  //   : [];

  const barData = (chartData ? getBarChartData(chartData) : []).sort((a, b) =>
    parseInt(a.Descriptor.slice(1)) > parseInt(b.Descriptor.slice(1)) ? 1 : -1,
  );
  const measureData = chartData ? getMeasureImpacts(chartData) : [];
  // console.log('measureData', measureData);
  // console.log('all', chartData);
  // console.log('barData', barData);

  return (
    <div className="charts-intro-page">
      {chartData ? (
        <>
          <div id="content-text-target" ref={targetNode}>
            <div dangerouslySetInnerHTML={{ __html: outsideText }}></div>
          </div>
          <Grid columns="3" stackable>
            <Grid.Row>
              <Grid.Column>
                <div className="chart-wrapper">
                  <h3 className="chart-title">Measure impacts to</h3>
                  <PieChart data={measureData} valueFormat=">-.2%" />
                </div>
              </Grid.Column>
              <Grid.Column>
                <div className="chart-wrapper">
                  <h3 className="chart-title">Origin of the measure</h3>
                  <PieChart
                    data={getOriginOfMeasure(chartData)}
                    valueFormat=">-.2%"
                  />
                </div>
              </Grid.Column>
              <Grid.Column>
                <div className="chart-wrapper">
                  <h3 className="chart-title">Sectors</h3>
                  <PieChart data={getSectors(chartData)} valueFormat=">-.2%" />
                </div>
              </Grid.Column>
            </Grid.Row>
          </Grid>
          <Grid>
            <Grid.Row>
              <Grid.Column mobile={16} tablet={16} computer={16}>
                <div className="chart-wrapper" style={{ height: '500px' }}>
                  <h3 className="chart-title">
                    Origin of the measure/Descriptors
                  </h3>
                  <BarChart
                    data={barData}
                    keys={Object.keys(barData[1] || {}) // [0] doesn't have all keys
                      .filter((k) => k !== 'Descriptor')
                      .sort()}
                    indexBy="Descriptor"
                  />
                </div>
              </Grid.Column>
            </Grid.Row>

            <Grid.Row>
              <Grid.Column mobile={16} tablet={16} computer={16}>
                <OriginTable
                  data={barData}
                  columns={barData.map(({ Descriptor }) => Descriptor)}
                  rows={Object.keys(barData[1] || {})
                    .filter((k) => k !== 'Descriptor')
                    .sort()}
                />
              </Grid.Column>
            </Grid.Row>
          </Grid>
        </>
      ) : (
        ''
      )}
    </div>
  );
};

export default ChartsIntro;
