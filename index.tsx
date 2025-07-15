/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
// Fix: Changed FunctionResponsePart to FunctionResponse as it's the correctly exported type.
import { GoogleGenAI, mcpToTool, FunctionResponse } from '@google/genai';
import { ChatState, marked, Playground, Product } from './playground';

import { startMcpGoogleMapServer, Episode } from './mcp_maps_server'; // Import Episode type

/* --------- */


async function startClient(transport: Transport) {
  const client = new Client({ name: "AI Studio", version: "1.0.0" });
  await client.connect(transport);
  return client;
}

/* ------------ */


const SYSTEM_INSTRUCTIONS = `you're an extremely proficient AI assistant.
You can use tools to discover interesting places, find product information, or get details about TV show episodes.
When asked a question try to use tools to show related informations.
Always explain what are you doing.

Tool Usage Guidelines:
- Product Information: Use the 'get-wild-kratts-products' tool to fetch Wild Kratts products.
    - This tool has two modes of operation:
        1.  **Search Mode (when 'searchTerm' is provided):**
            - The tool will search across the entire product catalog for items matching the 'searchTerm' (and 'category' if also provided).
            - It returns up to the first 100 matching products.
            - The 'page' parameter is IGNORED in this mode.
            - The returned 'pagination' object will have 'currentPage: 1', and 'totalItems'/'totalPages' will reflect the scope of the items found by the search (up to the 100 returned if many more matched).
            - Available product categories to use with the 'category' filter are: "Accessorize", "Apps", "Bath & Body", "Bedding", "Celebrate", "Coloring", "Crafts & Activities", "Listen", "Play", "Posters", "Read", "STEM", "Watch", "Wear". If the user asks for a category not on this list (e.g., "books"), try to map it to the closest valid category (e.g., "Read") or use the 'searchTerm' instead.
        2.  **Browse Mode (when 'searchTerm' is NOT provided):**
            - The tool returns a paginated list of products, potentially filtered by 'category'.
            - Use the 'page' parameter (e.g., { page: 2 }) to request a specific page. It defaults to page 1.
            - The tool response includes a 'products' array and a 'pagination' object with 'currentPage', 'totalItems', and 'totalPages' reflecting the API's pagination for the (category-filtered) collection.
            - If 'totalPages' is greater than 'currentPage', you can fetch subsequent pages if more results are needed.
    - If you need to analyze or consider ALL products for a complex query, you might use the browse mode and fetch all pages sequentially, or if a relevant 'searchTerm' can be devised, use search mode (being mindful it returns up to 100 matches).

- Episode Information: Use the 'get-wild-kratts-episodes' tool to retrieve information about Wild Kratts TV episodes.
    - Filters: This tool can be filtered by 'seasonNumber' (e.g., { seasonNumber: 1 }), 'episodeTitle' (e.g., { episodeTitle: "Croc" }), and/or 'animalsFeatured' (e.g., { animalsFeatured: ["Lion", "Zebra"] }). These filters can be used together. The tool returns all matching episodes based on these filters.
    - Field Selection for Efficiency: For analytical queries (e.g., "What Creature Power has been used the most?"), you can request only specific data fields to reduce processing load and improve efficiency. Use the optional 'fields' parameter with an array of desired field names.
        - Example: { fields: ["Episode Title", "Creature Powers"] }
        - Valid field names for 'fields' are: "Season", "Episode Number (Broadcast Order)", "Episode Number (Internal)", "Episode Title", "Air Date", "imagePath", "Summary", "Animals Featured", "Creature Powers", "Locations", "streamingUrls".
        - If you use the 'fields' parameter, the tool will return objects containing only the requested fields.
        - Important: If you later need to display full episode details in the UI (e.g., using playground.displayEpisodes()), the UI expects all fields. In such cases, you might need to re-fetch the specific episodes without the 'fields' filter or with all necessary fields for display. For purely analytical results, displaying cards might not be necessary.

- Map Tools: The map related tools (view_location_google_maps, search_google_maps, directions_on_google_maps) are available but will not display a visual map; they will return textual information.

Handling Complex Queries:
For complex queries that require information from multiple sources (e.g., finding products related to a specific episode):
1.  Break down the query into smaller, manageable steps.
2.  Use the available tools sequentially to gather all necessary information. For instance, to find products relevant to a specific episode:
    a.  First, use 'get-wild-kratts-episodes' to get details about the episode. For analysis, use the 'fields' parameter to fetch only relevant data (e.g., its theme, animals featured, summary). If the query specifies an exact episode number within a season, you may need to fetch all episodes for that season (potentially with limited fields first) and then identify the specific episode from the results based on its "Episode Number (Broadcast Order)".
    b.  Then, use 'get-wild-kratts-products' (using search mode if a good term can be found, or browse mode fetching pages if necessary) to get a list of relevant products.
3.  Once you have all the necessary information, synthesize it to answer the user's question. For example, you might compare the episode's themes or featured animals with product descriptions or categories to suggest relevant products.
4.  Clearly explain your process to the user: what tools you used, what information you gathered, and how you arrived at your conclusion or recommendation. If you display information (like products or episodes), mention this. If a tool call yields no specific results, mention that as well.
`;

const EXAMPLE_PROMPTS = [
  'Where is something cool to see',
  'Show me San Francisco',
  'Where is a place with a tilted tower?',
  'Show me Mount Everest',
  'Can you show me Mauna Kea in Hawaii?',
  "Let's go to Venice, Italy.",
  'Take me to the northernmost capital city in the world',
  "How about the southernmost permanently inhabited settlement? What's it called and where is it?",
  'Show me the location of the ancient city of Petra in Jordan',
  "Let's jump to Machu Picchu in Peru",
  "Can you show me the Three Gorges Dam in China?",
  "Can you find a town or city with a really funny or unusual name and show it to me?",
  "Are there any Wild Kratts toys available?",
  "Show me Wild Kratts STEM products.",
  "Find Wild Kratts plush toys.",
  "Find all Wild Kratts magazines.",
  "Are there any products that mention 'adventure'?",
  "What kind of Wild Kratts merchandise can I buy? Show me page 1.",
  "Tell me about some Wild Kratts episodes.",
  "List all Wild Kratts episodes from season 1.",
  "Find the Wild Kratts episode titled 'Mom of a Croc'.",
  "What animals were featured in the Wild Kratts episodes from season 2 about cheetahs?",
  "Show me episodes from season 1 that feature crocodiles.",
  "Are there any episodes with lions and zebras?",
  "Analyze from all products the best products for episode 1 of season 7.",
  "What Creature Power has been used the most?"
];

// Fix: Initialize GoogleGenAI with apiKey from process.env
const ai = new GoogleGenAI({
  apiKey: process.env.API_KEY,
});

function createAiChat(mcpClient: Client) {
  return ai.chats.create({
    model: 'gemini-2.5-flash-preview-04-17',
    config: {
      systemInstruction: SYSTEM_INSTRUCTIONS,
      tools: [mcpToTool(mcpClient)],
    },
  });
}

function camelCaseToDash(str: string): string {
  return str
    .replace(/([a-z])([A-Z])/g, '$1-$2')
    .replace(/([A-Z])([A-Z][a-z])/g, '$1-$2')
    .toLowerCase();
}

document.addEventListener('DOMContentLoaded', async (event) => {
  const rootElement = document.querySelector('#root')! as HTMLElement;

  const playground = new Playground();
  rootElement.appendChild(playground as HTMLElement);

  const [transportA, transportB] = InMemoryTransport.createLinkedPair();

  void startMcpGoogleMapServer(transportA, () => {
    console.log("Map tool called, but visual map display is replaced by products/episodes UI.");
  });

  const mcpClient = await startClient(transportB);
  const aiChat = createAiChat(mcpClient);

  playground.sendMessageHandler = async (
    input: string,
    role: string,
  ) => {
    console.log(
      'sendMessageHandler',
      input,
      role
    );

    const { thinking, text } = playground.addMessage('assistant', '');
    
    playground.setChatState(ChatState.GENERATING);
    text.innerHTML = '...';

    let accumulatedText = '';
    let productToolCalledAndEmpty = false;
    let episodeToolCalledAndEmpty = false;
    
    try {
      const res = await aiChat.sendMessageStream({ message: input });

      for await (const chunk of res) {
        for (const candidate of chunk.candidates ?? []) {
          for (const part of candidate.content?.parts ?? []) {
            if (part.functionCall) {
              console.log('FUNCTION CALL:', part.functionCall.name, part.functionCall.args);
              const mcpCall = {
                name: camelCaseToDash(part.functionCall.name!),
                arguments: part.functionCall.args
              };

              const explanation = 'Calling function:\n```json\n' + JSON.stringify(mcpCall, null, 2) + '\n```';
              const { text: functionCallTextElement } = playground.addMessage('assistant', '');
              functionCallTextElement.innerHTML = await marked.parse(explanation);
            } else if (part.functionResponse) {
                const actualFunctionResponse = part.functionResponse;
                console.log('FUNCTION RESPONSE:', actualFunctionResponse.name, actualFunctionResponse.response);
                
                const toolResponsePayload = actualFunctionResponse.response as { content?: Array<{ type: string; text?: string }> };
                const toolResponseContent = toolResponsePayload?.content;

                if (actualFunctionResponse.name === 'get-wild-kratts-products') {
                    productToolCalledAndEmpty = false; // Reset flag
                    if (toolResponseContent && toolResponseContent[0] && typeof toolResponseContent[0].text === 'string') {
                        try {
                            const parsedData = JSON.parse(toolResponseContent[0].text);
                            // Expecting { products: Product[], pagination: {...} } or { error: string, products: [], pagination: {...} }
                            if (parsedData && parsedData.products && Array.isArray(parsedData.products)) {
                                playground.displayProducts(parsedData.products as Product[]);
                                if (parsedData.products.length === 0) {
                                    productToolCalledAndEmpty = true;
                                }
                                // AI will be informed about pagination via the tool response directly.
                            } else if (parsedData && typeof parsedData.error === 'string') {
                                console.error("Error from get-wild-kratts-products tool:", parsedData.error);
                                playground.displayProducts([]); // Display empty if error
                                accumulatedText += `\n\nSorry, I couldn't fetch product data: ${parsedData.error}`;
                                productToolCalledAndEmpty = true;
                            } else {
                                console.error("Unexpected data format from get-wild-kratts-products tool:", parsedData);
                                playground.displayProducts([]);
                                productToolCalledAndEmpty = true;
                            }
                        } catch (e) {
                            console.error("Failed to parse products from tool response:", e);
                            playground.displayProducts([]);
                            productToolCalledAndEmpty = true;
                        }
                    } else {
                         playground.displayProducts([]);
                         productToolCalledAndEmpty = true;
                    }
                } else if (actualFunctionResponse.name === 'get-wild-kratts-episodes') {
                    episodeToolCalledAndEmpty = false; // Reset flag
                    if (toolResponseContent && toolResponseContent[0] && typeof toolResponseContent[0].text === 'string') {
                        try {
                            const parsedData = JSON.parse(toolResponseContent[0].text);
                            if (Array.isArray(parsedData)) {
                                const episodes: Episode[] = parsedData as Episode[]; // Cast here
                                console.log("Fetched Wild Kratts episodes:", episodes);
                                // Important: If AI requested partial fields, UI might not render fully.
                                // AI should be guided to re-fetch with full fields if planning to display.
                                playground.displayEpisodes(episodes);
                                if (parsedData.length === 0) {
                                    episodeToolCalledAndEmpty = true;
                                }
                            } else if (parsedData && typeof parsedData.error === 'string') {
                                console.error("Error from get-wild-kratts-episodes tool:", parsedData.error);
                                playground.displayEpisodes([]);
                                accumulatedText += `\n\nSorry, I encountered an error trying to fetch episode data: ${parsedData.error}`;
                                if (text.innerHTML.trim() === '...') { 
                                    text.innerHTML = await marked.parse(accumulatedText);
                                }
                                episodeToolCalledAndEmpty = true;
                            } else {
                                console.error("Unexpected data format from get-wild-kratts-episodes tool:", parsedData);
                                playground.displayEpisodes([]);
                                episodeToolCalledAndEmpty = true;
                            }
                        } catch (e) {
                            console.error("Failed to parse episodes from tool response:", e);
                            playground.displayEpisodes([]);
                            episodeToolCalledAndEmpty = true;
                        }
                    } else {
                        playground.displayEpisodes([]);
                        episodeToolCalledAndEmpty = true;
                    }
                }
            } else if (part.text) {
              playground.setChatState(ChatState.GENERATING);
              accumulatedText += part.text;
              text.innerHTML = await marked.parse(accumulatedText);
            }
          }
        }
        playground.scrollToTheEnd();
      }
    } catch (e: any) {
      console.error('GenAI SDK Error:', e.message, e);
      let message = `Error: ${e.message}`;
      if (e.message && e.message.includes('{')) {
        const splitPos = e.message.indexOf('{');
        const msgJson = e.message.substring(splitPos);
        try {
          const sdkError = JSON.parse(msgJson);
          if (sdkError?.error?.message) {
            message = `Error: ${sdkError.error.message}`;
          }
        } catch (parseError) {
          console.error('Unable to parse the error message JSON:', parseError);
        }
      }
      const { text: errorTextElement } = playground.addMessage('error', '');
      errorTextElement.innerHTML = await marked.parse(message);
    }

    if (thinking && thinking.parentElement) {
      thinking.parentElement!.removeAttribute('open');
      if (thinking.innerHTML.trim() === '') {
         thinking.parentElement!.classList.add('hidden');
      }
    }

    if (accumulatedText.trim().length === 0 && text.innerHTML.trim() === '...') {
      const hasProductDisplay = playground.activeContentType === 'products' && playground.productsToDisplay && playground.productsToDisplay.length > 0;
      const hasEpisodeDisplay = playground.activeContentType === 'episodes' && playground.episodesToDisplay && playground.episodesToDisplay.length > 0;

      if (hasProductDisplay) {
        text.innerHTML = await marked.parse("Displayed products based on the tool's response.");
      } else if (hasEpisodeDisplay) {
        text.innerHTML = await marked.parse("Displayed episodes based on the tool's response.");
      } else if (productToolCalledAndEmpty) {
        text.innerHTML = await marked.parse("I searched for products based on your query but didn't find any matching items to display for the current page/filters.");
      } else if (episodeToolCalledAndEmpty) {
        text.innerHTML = await marked.parse("I searched for episodes based on your query but didn't find any matching items to display.");
      } else { 
         text.innerHTML = await marked.parse('Done.');
      }
    } else if (accumulatedText.trim().length > 0 && !text.innerHTML.includes(accumulatedText.trim())) {
        text.innerHTML = await marked.parse(accumulatedText);
    }


    playground.setChatState(ChatState.IDLE);
  };

  playground.setInputField(
    EXAMPLE_PROMPTS[Math.floor(Math.random() * EXAMPLE_PROMPTS.length)],
  );
  playground.displayProducts([]); 
});