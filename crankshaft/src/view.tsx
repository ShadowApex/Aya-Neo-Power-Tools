import { gamepadDialogClasses, PanelSection } from 'decky-frontend-lib';
import { Component, RenderableProps } from 'preact';

function onReady() {
  console.log('Ready!');
}

function PanelSectionTitle(props: RenderableProps<Component>) {
  return (
    <div class="quickaccesscontrols_PanelSectionTitle_2iFf9">
      {props.children}
    </div>
  );
}

class Body extends Component {
  onReady() {}
  render(props: RenderableProps<Component>) {
    return (
      <body
        onLoad={onReady}
        style="/*margin:0px;padding:0px;*/ overflow-x: hidden; margin: 0px"
      >
        {props.children}
      </body>
    );
  }
}

class BatteryInfo extends Component {
  updateBatteryStats() {}
  render(props: RenderableProps<Component>) {
    return (
      <div
        class="quickaccesscontrols_PanelSection_2C0g0"
        style="padding: 0px 4px"
        onClick={this.updateBatteryStats}
      ></div>
    );
  }
}

const body = (
  <Body>
    <PanelSection>
      <PanelSectionTitle></PanelSectionTitle>
    </PanelSection>
    <BatteryInfo />
  </Body>
);

export const modal = body;
