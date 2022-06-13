import { SMM } from './types/SMM';
import { body } from './view';

const PLUGIN_ID = 'aya-neo-powertools';
const TITLE = 'Aya Neo Power Tools';

export const load = (smm: SMM) => {
  console.info(`${TITLE} plugin loaded!`);

  const render = async () => {
    return body;
  };

  smm.InGameMenu.addMenuItem({
    id: PLUGIN_ID,
    title: TITLE,
    render: async (_smm: SMM, root) => {
      root.appendChild(await render());
    },
  });
};

export const unload = (smm: SMM) => {
  console.info(`${TITLE} plugin unloaded!`);
  smm.InGameMenu.removeMenuItem(PLUGIN_ID);
};
