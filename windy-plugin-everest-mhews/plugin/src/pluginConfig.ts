import type { ExternalPluginConfig } from '@windy/interfaces.d';

const config: ExternalPluginConfig = {
    name: 'windy-plugin-everest-mhews',
    version: '0.1.7',
    icon: '⛰',
    title: 'EVEREST MHEWS',
    description: 'Multi-hazard monitoring layers for the Everest region.',
    author: 'Everest MHEWS',
    repository: 'https://github.com/Yizebaba/Everest',
    desktopUI: 'rhpane',
    mobileUI: 'fullscreen',
    routerPath: '/everest-mhews',
    private: true,
};

export default config;
