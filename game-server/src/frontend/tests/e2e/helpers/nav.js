async function goToSection(page, sectionId) {
  await page.getByTestId(`nav-${sectionId}`).click();
  await page.getByTestId(`section-${sectionId}`).waitFor();
}

module.exports = { goToSection };

