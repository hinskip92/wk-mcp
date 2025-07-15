/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

// tslint:disable
import hljs from 'highlight.js';
import {html, LitElement, nothing} from 'lit';
import {customElement, query, state} from 'lit/decorators.js';
import {classMap} from 'lit/directives/class-map.js';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import {Marked} from 'marked';
import {markedHighlight} from 'marked-highlight';
import { Episode } from './mcp_maps_server'; // Import Episode type

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


/** Markdown formatting function with syntax hilighting */
export const marked = new Marked(
  markedHighlight({
    async: true,
    emptyLangClass: 'hljs',
    langPrefix: 'hljs language-',
    highlight(code, lang, info) {
      const language = hljs.getLanguage(lang) ? lang : 'plaintext';
      return hljs.highlight(code, {language}).value;
    },
  }),
);

const ICON_BUSY = html`<svg
  class="rotating"
  xmlns="http://www.w3.org/2000/svg"
  height="24px"
  viewBox="0 -960 960 960"
  width="24px"
  fill="currentColor">
  <path
    d="M480-80q-82 0-155-31.5t-127.5-86Q143-252 111.5-325T80-480q0-83 31.5-155.5t86-127Q252-817 325-848.5T480-880q17 0 28.5 11.5T520-840q0 17-11.5 28.5T480-800q-133 0-226.5 93.5T160-480q0 133 93.5 226.5T480-160q133 0 226.5-93.5T800-480q0-17 11.5-28.5T840-520q17 0 28.5 11.5T880-480q0 82-31.5 155t-86 127.5q-54.5 54.5-127 86T480-80Z" />
</svg>`;

const ICON_CHAT_SHOW = html`<svg xmlns="http://www.w3.org/2000/svg" height="28px" viewBox="0 -960 960 960" width="28px" fill="currentColor"><path d="M240-400h320v-80H240v80Zm0-120h480v-80H240v80Zm0-120h480v-80H240v80ZM80-80v-720q0-33 23.5-56.5T160-880h640q33 0 56.5 23.5T880-800v480q0 33-23.5 56.5T800-240H240L80-80Zm126-240h594v-480H160v525l46-45Zm-46 0v-480 480Z"/></svg>`;
const ICON_CHAT_HIDE = html`<svg xmlns="http://www.w3.org/2000/svg" height="28px" viewBox="0 -960 960 960" width="28px" fill="currentColor"><path d="m480-320 160-160-160-160-56 56 104 104-104 104 56 56ZM80-80v-720q0-33 23.5-56.5T160-880h640q33 0 56.5 23.5T880-800v480q0 33-23.5 56.5T800-240H240L80-80Zm126-240h594v-480H160v525l46-45Zm-46 0v-480 480Z"/></svg>`;


/**
 * Chat state enum to manage the current state of the chat interface.
 */
export enum ChatState {
  IDLE,
  GENERATING,
  THINKING, 
  EXECUTING,
}

/**
 * Chat tab enum to manage the current selected tab in the chat interface.
 */
enum ChatTab {
  GEMINI,
}

const MAX_PRODUCT_DESCRIPTION_LENGTH = 200;
const MAX_EPISODE_SUMMARY_LENGTH = 250;

/**
 * Playground component.
 */
@customElement('gdm-playground')
export class Playground extends LitElement {
  @query('#anchor') anchor?: HTMLDivElement;

  @state() chatState = ChatState.IDLE;
  @state() selectedChatTab = ChatTab.GEMINI;
  @state() inputMessage = '';
  @state() messages: HTMLElement[] = [];
  
  @state() productsToDisplay: Product[] = [];
  @state() episodesToDisplay: Episode[] = [];
  @state() activeContentType: 'products' | 'episodes' = 'products';

  @state() expandedProductDescriptionIds: Set<number> = new Set();
  @state() expandedEpisodeSummaryKeys: Set<string> = new Set();

  @state() chatPanelVisible: boolean = true;


  sendMessageHandler?: (input: string, role: string) => Promise<void>;

  constructor() {
    super();
  }

  createRenderRoot() {
    return this;
  }

  setChatState(state: ChatState) {
    this.chatState = state;
  }

  displayProducts(products: Product[]) {
    this.productsToDisplay = products;
    this.activeContentType = 'products';
    this.expandedProductDescriptionIds.clear(); // Reset expanded state on new products
    (this as LitElement).requestUpdate();
  }

  displayEpisodes(episodes: Episode[]) {
    this.episodesToDisplay = episodes;
    this.activeContentType = 'episodes';
    this.expandedEpisodeSummaryKeys.clear(); // Reset expanded state on new episodes
    (this as LitElement).requestUpdate();
  }

  private toggleChatPanel() {
    this.chatPanelVisible = !this.chatPanelVisible;
    this.requestUpdate();
  }

  private toggleProductDescription(productId: number) {
    if (this.expandedProductDescriptionIds.has(productId)) {
      this.expandedProductDescriptionIds.delete(productId);
    } else {
      this.expandedProductDescriptionIds.add(productId);
    }
    this.requestUpdate();
  }

  private toggleEpisodeSummary(episodeKey: string) {
    if (this.expandedEpisodeSummaryKeys.has(episodeKey)) {
      this.expandedEpisodeSummaryKeys.delete(episodeKey);
    } else {
      this.expandedEpisodeSummaryKeys.add(episodeKey);
    }
    this.requestUpdate();
  }

  setInputField(message: string) {
    this.inputMessage = message.trim();
  }

  addMessage(role: string, message: string) {
    const div = document.createElement('div');
    div.classList.add('turn');
    div.classList.add(`role-${role.trim()}`);

    const thinkingDetails = document.createElement('details');
    thinkingDetails.classList.add('hidden'); 
    const summary = document.createElement('summary');
    summary.textContent = 'Thinking...'; 
    thinkingDetails.append(summary); 

    thinkingDetails.classList.add('thinking');
    
    const thinking = document.createElement('div');
    thinkingDetails.append(thinking); 
    div.append(thinkingDetails); 

    const text = document.createElement('div');
    text.className = 'text';
    text.innerHTML = message; 
    div.append(text);

    this.messages.push(div);
    (this as LitElement).requestUpdate();
    this.scrollToTheEnd();
    return {thinking, text};
  }

  scrollToTheEnd() {
    if (!this.anchor) return;
    this.anchor.scrollIntoView({
      behavior: 'smooth',
      block: 'end',
    });
  }

  async sendMessageAction(message?: string, role?: string) {
    if (this.chatState !== ChatState.IDLE) return;

    this.chatState = ChatState.GENERATING;

    let msg = '';
    if (message) {
      msg = message.trim();
    } else {
      msg = this.inputMessage.trim();
      this.inputMessage = '';
    }

    if (msg.length === 0) {
      this.chatState = ChatState.IDLE;
      return;
    }

    const msgRole = role ? role.toLowerCase() : 'user';

    if (msgRole === 'user' && msg) {
      const parsedUserMessage = await marked.parse(msg);
      this.addMessage(msgRole, parsedUserMessage);
    }

    if (this.sendMessageHandler) {
      await this.sendMessageHandler(msg, msgRole);
    }
  }

  private async inputKeyDownAction(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      e.stopPropagation();
      this.sendMessageAction();
    }
  }

  renderProductCards() {
    if (!this.productsToDisplay || this.productsToDisplay.length === 0) {
      return html`<div class="no-content-message">
        <p>No products to display. Try asking "What Wild Kratts toys are available?"</p>
      </div>`;
    }
    return html`
      <div class="products-container">
        ${this.productsToDisplay.map(
          (product) => {
            const hasRetailers = product.retailers && product.retailers.length > 0;
            const description = product.description || '';
            const isExpanded = this.expandedProductDescriptionIds.has(product.id);
            const isLongDescription = description.length > MAX_PRODUCT_DESCRIPTION_LENGTH;

            return html`
            <div class="product-card">
              ${product.featured_image ? html`<img src="${product.featured_image}" alt="${product.title.rendered}" class="product-image">` : ''}
              <div class="product-content-wrapper">
                <h3>${product.title.rendered}</h3>
                <div class="product-description">
                  ${unsafeHTML(isLongDescription && !isExpanded ? description.substring(0, MAX_PRODUCT_DESCRIPTION_LENGTH) + '...' : description)}
                  ${isLongDescription ? html`
                    <button @click=${() => this.toggleProductDescription(product.id)} class="read-more-button">
                      ${isExpanded ? 'Read less' : 'Read more'}
                    </button>
                  ` : ''}
                </div>
                ${product.product_categories && product.product_categories.length > 0 ? 
                  html`<div class="product-categories"><strong>Categories:</strong> ${product.product_categories.join(', ')}</div>` : ''
                }
                <div class="product-links-container">
                  ${hasRetailers ? 
                    product.retailers!.map(retailer => html`
                      <a href=${retailer.product_url} target="_blank" rel="noopener noreferrer" class="retailer-link">
                        Buy at ${retailer.retailer_name}
                      </a>
                    `) :
                    html`<a href=${product.link} target="_blank" rel="noopener noreferrer" class="product-link">
                      View Product Details
                    </a>`
                  }
                </div>
              </div>
            </div>
          `
        })}
      </div>
    `;
  }

  renderEpisodeCards() {
    if (!this.episodesToDisplay || this.episodesToDisplay.length === 0) {
      return html`<div class="no-content-message">
        <p>No episodes match your criteria. Try a different search, like specifying a season, title, or featured animals.</p>
      </div>`;
    }
    return html`
      <div class="episodes-container">
        ${this.episodesToDisplay.map(
          (episode) => {
            const summary = episode.Summary || '';
            const episodeKey = `${episode.Season}-${episode["Episode Number (Broadcast Order)"]}`;
            const isSummaryExpanded = this.expandedEpisodeSummaryKeys.has(episodeKey);
            const isLongSummary = summary.length > MAX_EPISODE_SUMMARY_LENGTH;
            const hasStreamableUrls = episode.streamingUrls && typeof episode.streamingUrls === 'object' && Object.values(episode.streamingUrls).some(url => !!url);

            return html`
            <div class="episode-card">
              <img class="episode-image" src="${episode.imagePath}" alt="${episode["Episode Title"]}">
              <div class="episode-content">
                <h3 class="episode-title">${episode["Episode Title"]}</h3>
                <div class="episode-metadata">
                  Season ${episode.Season}, Episode ${episode["Episode Number (Broadcast Order)"]} | Air Date: ${episode["Air Date"]}
                </div>
                <div class="episode-summary">
                  ${unsafeHTML(isLongSummary && !isSummaryExpanded ? summary.substring(0, MAX_EPISODE_SUMMARY_LENGTH) + '...' : summary)}
                  ${isLongSummary ? html`
                    <button @click=${() => this.toggleEpisodeSummary(episodeKey)} class="read-more-button">
                      ${isSummaryExpanded ? 'Read less' : 'Read more'}
                    </button>
                  ` : ''}
                </div>
                
                ${episode["Animals Featured"] && episode["Animals Featured"].length > 0 ? html`
                  <div class="episode-details-section">
                    <h4>Animals Featured</h4>
                    <ul class="episode-tags">
                      ${episode["Animals Featured"].map(animal => html`<li>${animal}</li>`)}
                    </ul>
                  </div>
                ` : ''}

                ${episode["Creature Powers"] && episode["Creature Powers"].length > 0 ? html`
                  <div class="episode-details-section">
                    <h4>Creature Powers</h4>
                    <ul class="episode-list">
                      ${episode["Creature Powers"].map(cp => html`<li>${cp.power} (Used by: ${cp.used_by})</li>`)}
                    </ul>
                  </div>
                ` : ''}

                ${episode.Locations && episode.Locations.length > 0 ? html`
                  <div class="episode-details-section">
                    <h4>Locations</h4>
                    <ul class="episode-tags">
                      ${episode.Locations.map(location => html`<li>${location}</li>`)}
                    </ul>
                  </div>
                ` : ''}

                ${hasStreamableUrls ? html`
                  <div class="episode-streaming-links">
                    <h4>Watch On</h4>
                    ${Object.entries(episode.streamingUrls!).map(([name, url]) => 
                      url ? html`<a href="${url}" target="_blank" rel="noopener noreferrer" class="streaming-link">${name}</a>` : nothing
                    )}
                  </div>
                ` : ''}
              </div>
            </div>
          `
        })}
      </div>
    `;
  }


  render() {
    return html`<div class="playground">
      <div 
        class="chat-panel-hover ${classMap({ visible: this.chatPanelVisible })}"
      >
        <div class="selector">
          <button
            id="geminiTab"
            class=${classMap({
              'selected-tab': this.selectedChatTab === ChatTab.GEMINI,
            })}
            @click=${() => {
              this.selectedChatTab = ChatTab.GEMINI;
            }}>
            Gemini
          </button>
        </div>
        <div
          id="chat"
          class=${classMap({
            'tabcontent': true,
            'showtab': this.selectedChatTab === ChatTab.GEMINI,
          })}>
          <div class="chat-messages">
            ${this.messages}
            <div id="anchor"></div>
          </div>

          <div class="footer">
            <div
              id="chatStatus"
              class=${classMap({'hidden': this.chatState === ChatState.IDLE})}>
              ${this.chatState === ChatState.GENERATING
                ? html`${ICON_BUSY} Generating...`
                : nothing}
              ${this.chatState === ChatState.THINKING 
                ? html`${ICON_BUSY} Thinking...`
                : nothing}
              ${this.chatState === ChatState.EXECUTING
                ? html`${ICON_BUSY} Executing...`
                : nothing}
            </div>
            <div id="inputArea">
              <input
                type="text"
                id="messageInput"
                .value=${this.inputMessage}
                @input=${(e: InputEvent) => {
                  this.inputMessage = (e.target as HTMLInputElement).value;
                }}
                @keydown=${(e: KeyboardEvent) => {
                  this.inputKeyDownAction(e);
                }}
                placeholder="Type your message..."
                autocomplete="off" />
              <button
                id="sendButton"
                class=${classMap({
                  'disabled': this.chatState !== ChatState.IDLE,
                })}
                @click=${() => {
                  this.sendMessageAction();
                }}>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  height="30px"
                  viewBox="0 -960 960 960"
                  width="30px"
                  fill="currentColor">
                  <path d="M120-160v-240l320-80-320-80v-240l760 320-760 320Z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="main-container">
        ${this.activeContentType === 'episodes' ? this.renderEpisodeCards() : this.renderProductCards()}
      </div>

      <button 
        class="chat-toggle-button"
        @click=${this.toggleChatPanel}
        title=${this.chatPanelVisible ? "Hide Chat" : "Show Chat"}
      >
        ${this.chatPanelVisible ? ICON_CHAT_HIDE : ICON_CHAT_SHOW}
      </button>
    </div>`;
  }
}
