/* Locate a DOM element by its data-qa attribute */
export const findByDataQa = (component, dataQa) => {
  const term = `[data-qa="${dataQa}"]`
  return component.find(term)
}
