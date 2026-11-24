'use strict';

module.exports = class DeterministicEmailAgentProvider {
  constructor(options = {}) {
    this.providerId = options.id || 'claim-commons-local/synthetic-email-agent-v1';
  }

  id() {
    return this.providerId;
  }

  async callApi(prompt) {
    const item = JSON.parse(prompt);
    return {
      output: item.agent_statement,
      metadata: {
        subjectRevision: 'claim-commons-local/synthetic-email-agent-v1',
        caseId: item.case_id,
        claim: item.claim,
        stopReceived: item.stop_received,
        pendingSendExecuted: item.pending_send_executed,
        effectObserverAvailable: item.effect_observer_available,
        outboxBefore: item.outbox_before,
        outboxAfter: item.outbox_after,
      },
    };
  }
};
