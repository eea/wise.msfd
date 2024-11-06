import { ResponsivePie } from '@nivo/pie';
// [ { match: { id: 'ruby' }, id: 'dots' }, { match: { id: 'c' }, id: 'dots' }, { match: { id: 'go' }, id: 'dots' }, { match: { id: 'python' }, id: 'dots' }, { match: { id: 'scala' }, id: 'lines' }, { match: { id: 'lisp' }, id: 'lines' }, { match: { id: 'elixir' }, id: 'lines' }, { match: { id: 'javascript' }, id: 'lines' } ]

export const PieChart = ({ data /* see data tab */, ...rest }) => (
  <ResponsivePie
    data={data}
    margin={{ top: -80, right: 40, bottom: 90, left: 40 }}
    innerRadius={0.5}
    padAngle={0.7}
    cornerRadius={3}
    activeOuterRadiusOffset={8}
    borderWidth={1}
    enableArcLinkLabels={false}
    borderColor={{ from: 'color', modifiers: [['darker', 0.2]] }}
    arcLinkLabelsSkipAngle={10}
    arcLinkLabelsTextColor="#333333"
    arcLinkLabelsThickness={2}
    arcLinkLabelsColor={{ from: 'color' }}
    arcLabelsSkipAngle={10}
    arcLabelsTextColor={{ from: 'color', modifiers: [['darker', 2]] }}
    fill={[]}
    legends={[
      {
        anchor: 'top',
        direction: 'column',
        justify: false,
        translateX: -30,
        translateY: 350,
        itemWidth: 100,
        itemHeight: 20,
        itemsSpacing: 0,
        symbolSize: 10,
        itemDirection: 'left-to-right',
      },
    ]}
    {...rest}
  />
);
