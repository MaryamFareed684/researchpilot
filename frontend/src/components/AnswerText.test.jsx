import { fireEvent, render, screen } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import AnswerText from './AnswerText.jsx'

test('model output is shown as text and never becomes HTML', () => {
  const { container } = render(
    <AnswerText text={'<script>alert(1)</script> <img src=x onerror=alert(2)> hello'} />,
  )
  expect(container.querySelector('script')).toBeNull()
  expect(container.querySelector('img')).toBeNull()
  expect(container.textContent).toContain('<script>alert(1)</script>')
})

test('citations become buttons that report their number', () => {
  const onCite = vi.fn()
  render(<AnswerText text={'Plants use light [1]. Roads were built [2, 3].'} onCite={onCite} />)
  fireEvent.click(screen.getByRole('button', { name: 'Show source 2' }))
  expect(onCite).toHaveBeenCalledWith(2)
  expect(screen.getAllByRole('button')).toHaveLength(3)
})

test('headings, bullets and bold are understood', () => {
  render(<AnswerText text={'## Methodology\n- **Data used**: tweets [1]\n- second point'} />)
  expect(screen.getByRole('heading', { name: 'Methodology' })).toBeTruthy()
  expect(screen.getAllByRole('listitem')).toHaveLength(2)
  expect(screen.getByText('Data used').tagName).toBe('STRONG')
})