/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

// tslint:disable
import {McpServer} from '@modelcontextprotocol/sdk/server/mcp.js';
import {Transport} from '@modelcontextprotocol/sdk/shared/transport.js';
import {z} from 'zod';

export interface MapParams {
  location?: string;
  search?: string;
  origin?: string;
  destination?: string;
}

export interface Product {
  id: number;
  link: string;
  title: {
    rendered: string;
  };
  description?: string; // HTML content
  featured_image?: string; // URL
  product_categories?: string[];
  retailers?: Array<{ retailer_name: string; product_url: string; }>;
}

// New interfaces for Episode data
interface CreaturePower {
  power: string;
  used_by: string;
}

interface StreamingUrls {
  "PBS KIDS"?: string;
  "Netflix"?: string;
  "TVO KIDS"?: string;
  "Knowledge Network"?: string;
  "Amazon Prime Video"?: string;
  [key: string]: string | undefined; // For any other potential streaming services
}

export interface Episode {
  Season: number;
  "Episode Number (Broadcast Order)": number;
  "Episode Number (Internal)": number;
  "Episode Title": string;
  "Air Date": string;
  imagePath: string;
  Summary: string;
  "Animals Featured": string[];
  "Creature Powers": CreaturePower[];
  Locations: string[];
  streamingUrls: StreamingUrls;
}

// Define valid keys for the Episode interface, used for the 'fields' parameter
const VALID_EPISODE_FIELDS: (keyof Episode)[] = [
  "Season",
  "Episode Number (Broadcast Order)",
  "Episode Number (Internal)",
  "Episode Title",
  "Air Date",
  "imagePath",
  "Summary",
  "Animals Featured",
  "Creature Powers",
  "Locations",
  "streamingUrls"
];


export async function startMcpGoogleMapServer(
  transport: Transport,
  mapQueryHandler: (params: MapParams) => void,
) {
  const server = new McpServer({
    name: 'AI Studio Backend Tools',
    version: '1.0.0',
  });

  server.tool(
    'view_location_google_maps',
    'View a specific query or geographical location. Returns textual confirmation.',
    {query: z.string()},
    async ({query}) => {
      mapQueryHandler({location: query});
      return {
        content: [{type: 'text', text: `Information for location: ${query} would be processed.`}],
      };
    },
  );

  server.tool(
    'search_google_maps',
    'Search for places near a location. Returns textual confirmation.',
    {search: z.string()},
    async ({search}) => {
      mapQueryHandler({search});
      return {
        content: [{type: 'text', text: `Search results for: ${search} would be processed.`}],
      };
    },
  );

  server.tool(
    'directions_on_google_maps',
    'Get directions from an origin to a destination. Returns textual confirmation.',
    {origin: z.string(), destination: z.string()},
    async ({origin, destination}) => {
      mapQueryHandler({origin, destination});
      return {
        content: [
          {type: 'text', text: `Directions from ${origin} to ${destination} would be processed.`},
        ],
      };
    },
  );

  server.tool(
    'get-wild-kratts-products',
    'Fetches Wild Kratts products. If searchTerm is provided, it searches across the catalog for up to 100 matching items, ignoring the page parameter. Otherwise, it returns a paginated list. Can be filtered by category. Returns an object with products and pagination details.',
    {
      searchTerm: z.string().optional(),
      category: z.string().optional(),
      page: z.number().int().positive().optional().default(1),
    },
    async ({ searchTerm, category, page }) => {
      const perPage = 100;

      try {
        if (searchTerm) {
          // Exhaustive search when searchTerm is provided
          let accumulatedMatchingProducts: Product[] = [];
          let currentApiPage = 1;
          let totalApiPages = 1; // Will be updated after first fetch

          while (currentApiPage <= totalApiPages && accumulatedMatchingProducts.length < perPage) {
            const response = await fetch(`https://wildkratts.com/wp-json/wp/v2/products?per_page=${perPage}&page=${currentApiPage}`);
            if (!response.ok) {
              // If a subsequent page fetch fails, return what we have so far or handle error
              console.warn(`API request for page ${currentApiPage} failed with status ${response.status}. Returning accumulated results.`);
              break;
            }

            if (currentApiPage === 1) {
                totalApiPages = parseInt(response.headers.get('X-WP-TotalPages') || '1', 10);
            }
            
            let apiProducts: any[] = await response.json();
            if (!apiProducts || apiProducts.length === 0) { // No more products from API
              break;
            }

            let pageProducts: Product[] = apiProducts.map(p => ({
              id: p.id,
              link: p.link,
              title: p.title,
              description: p.description,
              featured_image: p.featured_image,
              product_categories: p.product_categories,
              retailers: p.retailers,
            }));

            // Apply searchTerm filter
            const lowerCaseSearchTerm = searchTerm.toLowerCase();
            pageProducts = pageProducts.filter(p => {
              const titleMatch = p.title.rendered.toLowerCase().includes(lowerCaseSearchTerm);
              const strippedDescription = p.description ? p.description.replace(/<[^>]*>/g, '').toLowerCase() : '';
              const descriptionMatch = strippedDescription.includes(lowerCaseSearchTerm);
              return titleMatch || descriptionMatch;
            });

            // Apply category filter if provided
            if (category) {
              const lowerCaseCategory = category.toLowerCase();
              pageProducts = pageProducts.filter(p => 
                p.product_categories && p.product_categories.some(cat => cat.toLowerCase().includes(lowerCaseCategory))
              );
            }
            
            accumulatedMatchingProducts.push(...pageProducts);
            
            if (accumulatedMatchingProducts.length >= perPage) {
              break; 
            }
            currentApiPage++;
          }
          
          const totalMatchingItemsFound = accumulatedMatchingProducts.length; 

          const responsePayload = {
            products: accumulatedMatchingProducts.slice(0, perPage),
            pagination: {
              currentPage: 1, 
              totalItems: totalMatchingItemsFound, 
              totalPages: Math.ceil(totalMatchingItemsFound / perPage) || 1, 
              itemsPerPage: perPage
            }
          };
          return { content: [{type: 'text', text: JSON.stringify(responsePayload)}] };

        } else {
          // Original paginated browsing logic (no searchTerm)
          const response = await fetch(`https://wildkratts.com/wp-json/wp/v2/products?per_page=${perPage}&page=${page}`);
          if (!response.ok) {
            throw new Error(`API request failed with status ${response.status}`);
          }
          
          const totalItemsHeader = response.headers.get('X-WP-Total');
          const totalPagesHeader = response.headers.get('X-WP-TotalPages');

          const totalItems = totalItemsHeader ? parseInt(totalItemsHeader, 10) : 0;
          const totalPages = totalPagesHeader ? parseInt(totalPagesHeader, 10) : 0;

          let apiProducts: any[] = await response.json();
          if (!apiProducts) { 
            apiProducts = [];
          }
          
          let filteredProducts: Product[] = apiProducts.map(p => ({
            id: p.id,
            link: p.link,
            title: p.title,
            description: p.description,
            featured_image: p.featured_image,
            product_categories: p.product_categories,
            retailers: p.retailers,
          }));

          // Filter by category if provided (searchTerm is not present here)
          if (category) {
            const lowerCaseCategory = category.toLowerCase();
            filteredProducts = filteredProducts.filter(p => 
              p.product_categories && p.product_categories.some(cat => cat.toLowerCase().includes(lowerCaseCategory))
            );
          }
          
          const responsePayload = {
            products: filteredProducts,
            pagination: {
              currentPage: page,
              totalItems: totalItems, 
              totalPages: totalPages, 
              itemsPerPage: perPage
            }
          };
          return { content: [{type: 'text', text: JSON.stringify(responsePayload)}] };
        }
      } catch (error: any) {
        console.error('Error fetching Wild Kratts products:', error);
        const errorPagination = { currentPage: searchTerm ? 1 : page, totalItems: 0, totalPages: 0, itemsPerPage: perPage };
        return {
          content: [{type: 'text', text: JSON.stringify({ error: `Error fetching products: ${error.message}`, products: [], pagination: errorPagination })}],
        };
      }
    },
  );

  server.tool(
    'get-wild-kratts-episodes',
    'Fetches a list of Wild Kratts episodes. Can be filtered by seasonNumber, episodeTitle, animalsFeatured, and/or specific fields to return for efficiency. Returns episode data as a JSON string.',
    {
      seasonNumber: z.number().optional(),
      episodeTitle: z.string().optional(),
      animalsFeatured: z.array(z.string()).optional(),
      fields: z.array(z.string()).optional(), // New 'fields' parameter
    },
    async ({seasonNumber, episodeTitle, animalsFeatured, fields}) => {
      try {
        const response = await fetch('https://wildkratts.com/wp-json/wild-kratts/v1/episodes');
        if (!response.ok) {
          throw new Error(`API request failed with status ${response.status}`);
        }
        let allApiEpisodes: Episode[] = await response.json();

        if (!allApiEpisodes || allApiEpisodes.length === 0) {
          return {
            content: [{type: 'text', text: JSON.stringify([])}],
          };
        }

        let filteredEpisodes = allApiEpisodes;

        // Filter by seasonNumber if provided
        if (seasonNumber !== undefined) {
          filteredEpisodes = filteredEpisodes.filter(ep => ep.Season === seasonNumber);
        }

        // Filter by episodeTitle if provided (case-insensitive partial match)
        if (episodeTitle) {
          const lowerCaseTitleQuery = episodeTitle.toLowerCase();
          filteredEpisodes = filteredEpisodes.filter(ep => ep["Episode Title"].toLowerCase().includes(lowerCaseTitleQuery));
        }

        // Filter by animalsFeatured if provided (episode must feature ALL specified animals)
        if (animalsFeatured && animalsFeatured.length > 0) {
          filteredEpisodes = filteredEpisodes.filter(ep => {
            if (!Array.isArray(ep["Animals Featured"])) {
              return false; 
            }
            const episodeAnimalsLower = ep["Animals Featured"].map(a => a.toLowerCase());
            return animalsFeatured.every(queryAnimal => 
              episodeAnimalsLower.some(epAnimal => epAnimal.includes(queryAnimal.toLowerCase()))
            );
          });
        }
        
        let episodesToReturn: Episode[] | Partial<Episode>[] = filteredEpisodes;

        // If 'fields' parameter is provided and contains valid field names, transform the episodes
        if (fields && fields.length > 0) {
          // Fix: Ensure keys are strongly typed as keyof Episode for safe property access.
          const validKeysOfEpisode = fields.filter(
            (field): field is keyof Episode => (VALID_EPISODE_FIELDS as string[]).includes(field)
          );

          if (validKeysOfEpisode.length > 0) {
            episodesToReturn = filteredEpisodes.map(ep => {
              const partialEpisode: Partial<Episode> = {};
              for (const key of validKeysOfEpisode) { // key is now keyof Episode
                // Fix: Removed redundant 'if (key in ep)' check as 'key' is 'keyof Episode' and 'ep' is 'Episode'.
                // This simplifies type inference for the assignment below.
                partialEpisode[key] = ep[key];
              }
              return partialEpisode;
            });
          }
          // If fields were provided but none were valid, episodesToReturn remains filteredEpisodes (full objects from previous filters).
        }

        return {
          content: [{type: 'text', text: JSON.stringify(episodesToReturn)}],
        };
      } catch (error: any)
{
        console.error('Error fetching Wild Kratts episodes:', error);
        return {
          content: [{type: 'text', text: JSON.stringify({ error: `Error fetching episodes: ${error.message}` })}],
        };
      }
    },
  );

  await server.connect(transport);
  console.log('MCP server running with Maps (non-visual), Products (with filtering & pagination), and Episodes tools (with enhanced filtering and field selection)');
  while (true) {
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
}