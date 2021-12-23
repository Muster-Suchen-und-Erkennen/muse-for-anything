import { bindable } from "aurelia-framework";
import { DataItemModel } from "./ontology-graph";
 
export class TreeNode {
  @bindable current: DataItemModel;
}
