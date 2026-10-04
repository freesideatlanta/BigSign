const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

class Element {
  constructor() {
    this.style = {};
    this.children = [];
    this.fields = new Map();
    this.textContent = '';
    this.clientHeight = 800;
    this.scrollHeight = 300;
    this.markup = '';
  }
  set innerHTML(value) {
    this.markup = value;
    this.children = [];
    this.fields.clear();
  }
  get innerHTML() { return this.markup; }
  appendChild(child) { this.children.push(child); }
  querySelector(selector) {
    assert.ok(this.markup.includes(`class="${selector.slice(1)}"`));
    if (!this.fields.has(selector)) this.fields.set(selector, new Element());
    return this.fields.get(selector);
  }
}

function loadSign() {
  const html = readFileSync(join(__dirname, '..', 'freeside-sign.html'), 'utf8');
  const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
  const elements = new Map();
  const context = vm.createContext({
    document: {
      getElementById(id) {
        if (!elements.has(id)) elements.set(id, new Element());
        return elements.get(id);
      },
      createElement: () => new Element(),
    },
    setInterval: () => 1,
    setTimeout: () => 1,
    clearTimeout: () => {},
    requestAnimationFrame: () => 1,
    cancelAnimationFrame: () => {},
    window: { addEventListener: () => {} },
    console,
  });
  // Exercise the real page functions while controlling initialization and timers.
  vm.runInContext(script.replace(/init\(\);\s*$/, ''), context);
  return { elements, run: code => vm.runInContext(code, context) };
}

test('event text remains literal instead of entering HTML markup', () => {
  const { elements, run } = loadSign();
  run(`events = [{title: 'Workshop <em> & friends', time: '06:30PM',
    source: 'Meetup', attendees: 3, free: true,
    index: Date.parse('2026-10-05T00:30:00Z') / 1000}]; buildCards();`);
  const [separator, card] = elements.get('scrollTrack').children;
  assert.equal(card.querySelector('.event-title').textContent, 'Workshop <em> & friends');
  assert.equal(card.querySelector('.event-time-text').textContent, '06:30PM');
  assert.equal(card.querySelector('.event-source').textContent, 'Meetup');
  assert.equal(card.querySelector('.attendee-count').textContent, '3 going');
  assert.ok(!card.innerHTML.includes('Workshop'));
  // UTC midnight still belongs to the previous calendar day in Atlanta.
  assert.ok(separator.innerHTML.includes('Sunday, Oct 4'));
});
