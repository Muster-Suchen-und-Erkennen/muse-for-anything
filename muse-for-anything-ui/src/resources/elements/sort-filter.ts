import { bindable, bindingMode, observable } from "aurelia-framework";
import { nanoid } from "nanoid";
import { CollectionFilter } from "rest/api-objects";


export class SortFilter {
    @bindable filter: CollectionFilter;
    @bindable currentValue: string | null;
    @bindable({ defaultBindingMode: bindingMode.fromView }) sortString: string | null = null;

    slug = nanoid(8);

    @observable() current: string[] = [];
    available: string[] = [];

    sortKeyToName: { [props: string]: string } = {};

    private allOptions = [];

    filterChanged(newValue, oldValue) {
        const sortKeyToName = {};
        const allOptions = [];

        this.filter.options.forEach(option => {
            if (option.name) {
                sortKeyToName[option.value] = option.name;
            }
            allOptions.push(option.value);
        });

        this.sortKeyToName = sortKeyToName;
        this.allOptions = allOptions;

        this.updateAvailable();
    }

    private updateAvailable() {
        const current = this.current.map(s => s.substring(1));
        this.available = this.allOptions.filter(s => !current.includes(s));
    }

    currentValueChanged(newValue, oldValue) {
        if (newValue == null) {
            this.current = [];
            return;
        }
        this.current = newValue.split(",")
            .filter(s => Boolean(s))
            .map(s => {
                if (s.startsWith("-") || s.startsWith("+")) {
                    return s;
                }
                return `+${s}`;  // default ascending
            });
        this.updateAvailable();
    }

    currentChanged(newValue, oldValue) {
        if (newValue && newValue.length > 0) {
            this.sortString = newValue.map(s => {
                if (s.startsWith("+")) {
                    return s.substring(1);
                }
                return s;  // only keep "-" prefix
            }).join(",");
        } else {
            this.sortString = null;
        }
    }

    addToCurrent(sortKey: string) {
        this.current = [...this.current, `+${sortKey}`];
        this.available = this.available.filter(key => key !== sortKey);
    }

    toggleOrRemove(sortKey: string) {
        const asc = `+${sortKey}`;
        const desc = `-${sortKey}`;
        if (this.current.includes(desc)) {
            this.removeFromCurrent(sortKey);
            return;
        }
        this.current = this.current.map(sort => {
            if (sort === asc) {
                return desc;
            }
            return sort;
        });
    }

    toggleDirection(sortKey: string) {
        const asc = `+${sortKey}`;
        const desc = `-${sortKey}`;
        this.current = this.current.map(sort => {
            if (sort === asc) {
                return desc;
            }
            if (sort === desc) {
                return asc;
            }
            return sort;
        });
    }

    removeFromCurrent(sortKey: string) {
        const asc = `+${sortKey}`;
        const desc = `-${sortKey}`;
        this.current = this.current.filter(sort => sort !== asc && sort !== desc);
        this.updateAvailable();
    }

}

