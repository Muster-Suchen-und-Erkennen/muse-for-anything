import { autoinject, bindingMode } from "aurelia-framework";
import { SignalBindingBehavior } from "aurelia-templating-resources";

const INTERCEPT_METHOD = "updateSource";

@autoinject
export class TeeBindingBehavior {

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
            updateInterceptor(value, binding);
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
