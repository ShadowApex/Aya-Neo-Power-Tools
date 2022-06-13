import { render } from 'preact';
import { SMM } from './types/SMM';
import { App } from './view';

const PLUGIN_ID = 'aya-neo-powertools';
const TITLE = 'Aya Neo Power Tools';

export const load = (smm: SMM) => {
  console.info(`${TITLE} plugin loaded!`);

  // Add quickaccess menu
  smm.InGameMenu.addMenuItem({
    id: PLUGIN_ID,
    title: TITLE,
    render: async (smm: SMM, root: HTMLElement) =>
      render(<App smm={smm} />, root),
  });
};

export const unload = (smm: SMM) => {
  console.info(`${TITLE} plugin unloaded!`);
  smm.InGameMenu.removeMenuItem(PLUGIN_ID);
};
