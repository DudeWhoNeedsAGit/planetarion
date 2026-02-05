async function goToSection(page, sectionId) {
  if (['wheel', 'alliance', 'messages'].includes(sectionId)) {
    await page.getByTestId('nav-more').click();
  }
  await page.getByTestId(`nav-${sectionId}`).click();
  await page.getByTestId(`section-${sectionId}`).waitFor();
}

module.exports = { goToSection };
