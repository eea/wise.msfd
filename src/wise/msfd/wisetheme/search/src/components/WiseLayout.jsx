import React from 'react';
import { Grid } from 'semantic-ui-react';

const RightColumnLayout = (props) => {
  const { bodyContent, bodyFooter, bodyHeader, header, sideContent } = props;
  return (
    <div>
      <Grid columns={2} stackable className="body-content">
        <Grid.Row>
          <Grid.Column widescreen={12}>
            <div>{header}</div>
            <div>{bodyHeader}</div>
            <div>{bodyContent}</div>
          </Grid.Column>
          <Grid.Column widescreen="4">
            <h3>Filter by</h3>
            <div>{sideContent}</div>
          </Grid.Column>
        </Grid.Row>
      </Grid>
      <Grid className="body-footer">
        <Grid.Row>
          <Grid.Column widescreen={12}>{bodyFooter}</Grid.Column>
        </Grid.Row>
      </Grid>
    </div>
  );
};

export default RightColumnLayout;
