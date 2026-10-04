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
    this.listeners = new Map();
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
  addEventListener(type, callback) { this.listeners.set(type, callback); }
  querySelector(selector) {
    assert.ok(this.markup.includes(`class="${selector.slice(1)}"`));
    if (!this.fields.has(selector)) this.fields.set(selector, new Element());
    return this.fields.get(selector);
  }
}

function loadSign(fetch = async () => { throw new Error("Network unavailable"); }) {
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
    fetch,
    console: { error: () => {} },
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
  assert.ok(!card.innerHTML.includes('event-source'));
  assert.ok(!card.innerHTML.includes('Meetup'));
  assert.equal(card.querySelector('.attendee-count').textContent, '3 going');
  assert.ok(!card.innerHTML.includes('Workshop'));
  // UTC midnight still belongs to the previous calendar day in Atlanta.
  assert.ok(separator.innerHTML.includes('Sunday, Oct 4'));
});

test('empty and fitting event lists stay at the top', () => {
  for (const height of [0, 300, 800]) {
    const { elements, run } = loadSign();
    run('getHeights();');
    elements.get('scrollTrack').scrollHeight = height;
    run('getHeights(); scrollStep(100); pausing = false; scrollStep(1100);');
    assert.match(elements.get('scrollTrack').style.transform, /^translateY\(-?0px\)$/);
    assert.equal(run('scrollY'), 0);
  }
});

test('overflow scrolls within bounds and clamps after a resize', () => {
  const { elements, run } = loadSign();
  run('getHeights();');
  elements.get('scrollTrack').scrollHeight = 1000;
  run('getHeights(); scrollStep(100); pausing = false; scrollStep(1100);');
  assert.equal(run('scrollY'), 30);
  run('scrollStep(10100);');
  assert.equal(run('scrollY'), 200);
  assert.equal(run('scrollDir'), -1);
  run('pausing = false; scrollStep(11100);');
  assert.equal(run('scrollY'), 0);
  assert.equal(run('scrollDir'), 1);
  run('pausing = false; scrollStep(12100);');
  elements.get('scrollWrapper').clientHeight = 1200;
  run('getHeights();');
  assert.equal(run('scrollY'), 0);
  assert.match(elements.get('scrollTrack').style.transform, /^translateY\(-?0px\)$/);
});

test('event images use the supplied URL and missing images leave the date visible', () => {
  const { elements, run } = loadSign();
  run(`events = [
    {title: 'With image', time: '06:30PM', attendees: 0, free: true,
      index: Date.parse('2026-10-05T00:30:00Z') / 1000,
      image_url: 'https://example.com/event.jpg'},
    {title: 'Without image', time: '07:30PM', attendees: 0, free: true,
      index: Date.parse('2026-10-05T01:30:00Z') / 1000, image_url: null}
  ]; buildCards();`);
  const [, withImage, withoutImage] = elements.get('scrollTrack').children;
  const [image] = withImage.querySelector('.event-visual').children;
  assert.equal(image.src, 'https://example.com/event.jpg');
  assert.equal(image.alt, '');
  assert.equal(withoutImage.querySelector('.event-visual').children.length, 0);
  assert.ok(withoutImage.innerHTML.includes('event-date-block'));
  image.listeners.get('error')();
  assert.equal(image.hidden, true);
  assert.match(elements.get('errorFooter').textContent, /Failed to load event image for With image/);
});

test('refresh errors show the message and retain events, then recovery hides the footer', async () => {
  let fails = true;
  const { elements, run } = loadSign(async () => {
    if (fails) return { ok: false, status: 503 };
    return { ok: true, json: async () => [] };
  });
  run(`events = [{title: 'Existing event', time: '06:30PM', attendees: 0, free: true,
    index: Date.parse('2026-10-05T00:30:00Z') / 1000}]; buildCards();`);
  const previousCards = elements.get('scrollTrack').children;
  await run('init();');
  assert.equal(elements.get('errorFooter').hidden, false);
  assert.match(elements.get('errorFooter').textContent, /HTTP 503/);
  assert.equal(elements.get('scrollTrack').children, previousCards);
  fails = false;
  await run('init();');
  assert.equal(elements.get('errorFooter').hidden, true);
  assert.equal(elements.get('errorFooter').textContent, '');
});

test('network and rendering failures show their actual error messages', async () => {
  const network = loadSign();
  await network.run('init();');
  assert.equal(network.elements.get('errorFooter').textContent, 'Error: Network unavailable');
  const rendering = loadSign(async () => ({ ok: true, json: async () => [
    { index: 1e20, title: 'Invalid date' }
  ] }));
  await rendering.run('init();');
  assert.match(rendering.elements.get('errorFooter').textContent, /Invalid time value/);
});
