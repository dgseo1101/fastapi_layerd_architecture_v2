- [SRP](https://www.notion.so/TIL-14-2c5162bf5d348014857bef0609c57792?pvs=21)
- [OCP](https://www.notion.so/TIL-15-2c5162bf5d34808da6d0f7dc896e77ca?pvs=21)
- [LSP](https://www.notion.so/TIL-16-2c5162bf5d348055a46fd64ca6911098?pvs=21)
- [ISP](https://www.notion.so/TIL-18-2c5162bf5d3480d5b562fc3b92b6ac6f?pvs=21)
- [DIP](https://www.notion.so/TIL-13-2c5162bf5d34803e84dec641d49074ee?pvs=21)

위 SOLID 원칙을 준수한 보일러 플레이트 코드임.

기존 https://github.com/dgseo1101/fastapi_layerd_architecture 의 단점을 보완하기 위해 설계되었으며 지속적으로 업데이트 예정.

원칙상 ISP를 지키기 위해선, base repository와 base service에, client에서 사용하지 않는 메서드는 제외하는 것이 원칙적으론 맞으나, "개발 생산성" 을 올리자는 취지에 맞지 않기에 제외하고 진행하였음.

트랜잭션 관리를 위해 기존에선 repository에 전역 session으로 관리하였으나, 이를 해결하기 위해, uow를 Server DI Container로 두고, Service layer에서 트랜잭션을 명시적으로 관리해줌.

```

def _active_users_spec(self, page: int, page_size: int):
        return SpecChain([
            Where.of(self.model.deleted_at.is_(None)),
            OrderBy.of(self.model.id.desc()),
            Paginate(page=page, page_size=page_size),
        ])

    async def get_activate_users(self, page: int, page_size: int):
        return await self.get_datas(spec=self._active_users_spec(page, page_size))

    async def filter_department_users(self, page: int, page_size: int, department):
        spec = SpecChain([
            *self._active_users_spec(page, page_size).specs,
            Where.of(self.model.department == department),
        ])

        return await self.get_datas(spec=spec)

```


이는 SpecChain을 정의하고 이를 돌려서 사용하는 예시임.

전역적으로 적용해야하는 filtering이나 list + count와 같은 조건이 늘고, 권한에 따른 분리가 되어야할 때 SpecChain을 요긴하게 사용할 수 있을 것이며, 팀 내에 모든 개발자가 같은 코드를 작성해 나가는 “일관성있는” 코드를 만들 수 있게 될 것임.
