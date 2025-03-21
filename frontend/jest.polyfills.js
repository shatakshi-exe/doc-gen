/**
 * @note The block below contains polyfills for Node.js globals
 * required for Jest to function when running JSDOM tests.
 * These HAVE to be require's and HAVE to be in this exact
 * order, since "undici" depends on the "TextEncoder" global API.
 *
 * Consider migrating to a more modern test runner if
 * you don't want to deal with this.
 */

const { MessageChannel } = require('worker_threads');

Object.defineProperties(globalThis, {
  MessageChannel: { value: MessageChannel },
  MessagePort: { value: MessageChannel.prototype.port1.constructor },
})

const streams = require('web-streams-polyfill/ponyfill'); 

Object.defineProperties(globalThis, {
  ReadableStream: { value: streams.ReadableStream },
  WritableStream: { value: streams.WritableStream },
  TransformStream: { value: streams.TransformStream },
});

const { TextDecoder, TextEncoder } = require('node:util')

Object.defineProperties(globalThis, {
  TextDecoder: { value: TextDecoder },
  TextEncoder: { value: TextEncoder },
})

const { Blob } = require('node:buffer')
const { fetch, Headers, FormData, Request, Response } = require('undici')

Object.defineProperties(globalThis, {
  fetch: { value: fetch, writable: true },
  Blob: { value: Blob },
  Headers: { value: Headers },
  FormData: { value: FormData },
  Request: { value: Request },
  Response: { value: Response },
})
