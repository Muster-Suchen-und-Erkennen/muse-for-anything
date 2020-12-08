import { autoinject, bindingMode } from "aurelia-framework";
import { SignalBindingBehavior } from "aurelia-templating-resources";

@autoinject
export class ViewSignalBindingBehavior {

    constructor(private signalBindingBehavior: SignalBindingBehavior) { }

    bind(binding, source, signal, onUpdate) {
        // hijack update target to update source...
        binding.updateTarget = (newValue) => {
            const currentValue = binding.targetObserver.getValue();
            const oldValue = binding.targetObserver.oldValue;
            // just update the subscribers
            if (binding.targetObserver.hasSubscribers()) {
                binding.targetObserver.callSubscribers(currentValue, oldValue);
            }
        };
        // bind the signal behavior to the alias
        this.signalBindingBehavior.bind(binding, source, signal);
    }

    unbind(binding, source) {
        // unbind the signal behavior
        this.signalBindingBehavior.unbind(binding, source);
    }
}

/*
 if (!this.isBound) {
            return;
        }
        if (context === sourceContext) {
            oldValue = this.targetObserver.getValue(this.target, this.targetProperty);
            newValue = this.sourceExpression.evaluate(this.source, this.lookupFunctions);
            if (newValue !== oldValue) {
                this.updateTarget(newValue);
            }
            if (this.mode !== bindingMode.oneTime) {
                this._version++;
                this.sourceExpression.connect(this, this.source);
                this.unobserve(false);
            }
            return;
        }
        if (context === targetContext) {
            if (newValue !== this.sourceExpression.evaluate(this.source, this.lookupFunctions)) {
                this.updateSource(newValue);
            }
            return;
        }
        throw new Error('Unexpected call context ' + c


if (!binding.updateTarget) {
            throw new Error('Only property bindings and string interpolation bindings can be signaled.  Trigger, delegate and call bindings cannot be signaled.');
        }
        var signals = this.signals;
        if (names.length === 1) {
            var name_1 = names[0];
            var bindings = signals[name_1] || (signals[name_1] = []);
            bindings.push(binding);
            binding.signalName = name_1;
        }
        else if (names.length > 1) {
            var i = names.length;
            while (i--) {
                var name_2 = names[i];
                var bindings = signals[name_2] || (signals[name_2] = []);
                bindings.push(binding);
            }
            binding.signalName = names;
        }
        else {
            throw new Error('Signal name is required.');
        }



export class TBindingBehavior {
  static inject = [SignalBindingBehavior];

  constructor(signalBindingBehavior) {
    this.signalBindingBehavior = signalBindingBehavior;
  }

  bind(binding, source) {
    // bind the signal behavior
    this.signalBindingBehavior.bind(binding, source, 'aurelia-translation-signal');

    // rewrite the expression to use the TValueConverter.
    // pass through any args to the binding behavior to the TValueConverter
    let sourceExpression = binding.sourceExpression;

    // do create the sourceExpression only once
    if (sourceExpression.rewritten) {
      return;
    }
    sourceExpression.rewritten = true;

    let expression = sourceExpression.expression;
    sourceExpression.expression = new ValueConverter(
      expression,
      't',
      sourceExpression.args,
      [expression, ...sourceExpression.args]);
  }

  unbind(binding, source) {
    // unbind the signal behavior
    this.signalBindingBehavior.unbind(binding, source);
  }
}
*/
