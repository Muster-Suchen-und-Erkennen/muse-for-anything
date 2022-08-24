import { autoinject, TaskQueue } from "aurelia-framework";

const INTERCEPT_METHOD = "updateSource";

@autoinject
export class TeeBindingBehavior {

    private queue: TaskQueue;

    constructor(queue: TaskQueue) {
        this.queue = queue;
    }

    bind(binding, source, updateInterceptor) {
        // intercept updates to also call method
        const method = INTERCEPT_METHOD;
        if (!binding[method]) {
            return;
        }
        binding[`intercepted-${method}`] = binding[method];
        const update = binding[method].bind(binding);
        binding[method] = (value) => {
            update(value);
            this.queue.queueMicroTask(() => updateInterceptor(value, binding));
        };
    }

    unbind(binding, source) {
        // unbind the signal behavior
        const method = INTERCEPT_METHOD;
        if (!binding[method]) {
            return;
        }
        binding[method] = binding[`intercepted-${method}`];
        binding[`intercepted-${method}`] = null;
    }
}
