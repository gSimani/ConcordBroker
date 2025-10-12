/**
 * DeepWiki Repository Integrations
 * Connects to multiple knowledge repositories for enhanced capabilities
 */

class DeepWikiIntegrations {
  constructor() {
    this.repositories = {
      firecrawl: {
        url: 'https://deepwiki.com/gSimani/firecrawl',
        purpose: 'Web scraping and data extraction',
        enabled: true
      },
      memvid: {
        url: 'https://deepwiki.com/gSimani/memvid',
        purpose: 'Permanent memory management',
        enabled: true
      },
      localDeepResearcher: {
        url: 'https://deepwiki.com/langchain-ai/local-deep-researcher',
        purpose: 'Local research and analysis',
        enabled: true
      },
      langchain: {
        url: 'https://deepwiki.com/langchain-ai/langchain',
        purpose: 'LLM orchestration and chaining',
        enabled: true
      },
      transformers: {
        url: 'https://deepwiki.com/huggingface/transformers',
        purpose: 'ML model transformers',
        enabled: true
      },
      redis: {
        url: 'https://deepwiki.com/redis/redis',
        purpose: 'Caching and data structures',
        enabled: true
      },
      buildYourOwnX: {
        url: 'https://deepwiki.com/codecrafters-io/build-your-own-x',
        purpose: 'Learning and building patterns',
        enabled: true
      },
      algorithms: {
        url: 'https://deepwiki.com/TheAlgorithms/Python',
        purpose: 'Algorithm implementations',
        enabled: true
      },
      autoGPT: {
        url: 'http://deepwiki.com/Significant-Gravitas/AutoGPT',
        purpose: 'Autonomous agent patterns',
        enabled: true
      },
      javaGuide: {
        url: 'https://deepwiki.com/Snailclimb/JavaGuide',
        purpose: 'Java development patterns',
        enabled: true
      },
      youtubeDl: {
        url: 'https://deepwiki.com/ytdl-org/youtube-dl',
        purpose: 'Media download capabilities',
        enabled: true
      },
      puppeteer: {
        url: 'https://deepwiki.com/puppeteer/puppeteer',
        purpose: 'Browser automation',
        enabled: true
      },
      openWebUI: {
        url: 'https://deepwiki.com/open-webui/open-webui',
        purpose: 'Web UI components',
        enabled: true
      },
      shadcnUI: {
        url: 'https://deepwiki.com/shadcn-ui/ui',
        purpose: 'UI component library',
        enabled: true
      },
      n8n: {
        url: 'https://deepwiki.com/n8n-io/n8n',
        purpose: 'Workflow automation',
        enabled: true
      },
      advancedJava: {
        url: 'https://deepwiki.com/doocs/advanced-java',
        purpose: 'Advanced Java concepts',
        enabled: true
      },
      codeServer: {
        url: 'https://deepwiki.com/coder/code-server',
        purpose: 'Remote development server',
        enabled: true
      },
      syncthing: {
        url: 'https://deepwiki.com/syncthing/syncthing',
        purpose: 'File synchronization',
        enabled: true
      },
      interviews: {
        url: 'https://deepwiki.com/kdn251/interviews',
        purpose: 'Interview preparation',
        enabled: true
      },
      browserUse: {
        url: 'https://deepwiki.com/browser-use/browser-use',
        purpose: 'Browser automation patterns',
        enabled: true
      },
      marktext: {
        url: 'https://deepwiki.com/marktext/marktext',
        purpose: 'Markdown editing',
        enabled: true
      }
    };
  }

  async initialize() {
    console.log('📚 Initializing DeepWiki Integrations...');
    const enabled = Object.values(this.repositories).filter(r => r.enabled);
    console.log(`✅ ${enabled.length} DeepWiki repositories configured`);
  }

  async fetchKnowledge(repositoryName, query) {
    const repo = this.repositories[repositoryName];
    if (!repo || !repo.enabled) {
      throw new Error(`Repository ${repositoryName} not found or disabled`);
    }

    // This would integrate with DeepWiki API
    // For now, returning metadata
    return {
      repository: repositoryName,
      url: repo.url,
      purpose: repo.purpose,
      query,
      timestamp: new Date().toISOString()
    };
  }

  async searchAllRepositories(query) {
    const results = [];
    for (const [name, repo] of Object.entries(this.repositories)) {
      if (repo.enabled) {
        results.push({
          repository: name,
          url: repo.url,
          purpose: repo.purpose,
          relevance: this.calculateRelevance(query, repo.purpose)
        });
      }
    }

    return results.sort((a, b) => b.relevance - a.relevance);
  }

  calculateRelevance(query, purpose) {
    const queryLower = query.toLowerCase();
    const purposeLower = purpose.toLowerCase();
    const words = queryLower.split(' ');

    let score = 0;
    words.forEach(word => {
      if (purposeLower.includes(word)) {
        score += 1;
      }
    });

    return score;
  }

  getRepository(name) {
    return this.repositories[name];
  }

  getAllRepositories() {
    return this.repositories;
  }

  getEnabledRepositories() {
    return Object.entries(this.repositories)
      .filter(([_, repo]) => repo.enabled)
      .reduce((acc, [name, repo]) => {
        acc[name] = repo;
        return acc;
      }, {});
  }
}

module.exports = DeepWikiIntegrations;
