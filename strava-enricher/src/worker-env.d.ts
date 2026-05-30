// Ambient declaration for the plan YAML bundled as a text module at build time
// (Wrangler's `[[rules]] type = "Text"`). Tracked in git so a fresh checkout
// typechecks without first running `wrangler types`.
declare module "*.yaml" {
  const content: string;
  export default content;
}
