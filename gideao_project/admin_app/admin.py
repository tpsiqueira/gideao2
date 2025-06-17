from django.contrib import admin

from .models import (
    uo,
    grandeza_industrial,
    grandeza_especialista,
    ativo,
    uep,
    poco,
    variavel_industrial,
    relacao_especialista_industrial,
    unidade_medida_padrao,
    unidade_medida,
)


class uoAdmin(admin.ModelAdmin):
    model = uo
    search_fields = ("nome",)
    list_display = ("nome",)


admin.site.register(uo, uoAdmin)
admin.site.register(grandeza_industrial)


class geAdmin(admin.ModelAdmin):
    model = grandeza_especialista
    search_fields = ("nome",)
    list_display = (
        "nome",
        "rotulo_steady_state",
    )


admin.site.register(grandeza_especialista, geAdmin)


class ativoAdmin(admin.ModelAdmin):
    model = ativo
    search_fields = ("nome",)
    list_filter = ("uo__nome",)
    list_display = (
        "nome",
        "getUONome",
    )

    def getUONome(self, obj):
        return obj.uo.nome


admin.site.register(ativo, ativoAdmin)


class uepAdmin(admin.ModelAdmin):
    model = uep
    search_fields = ("nome",)
    list_filter = ("ativo__uo__nome",)
    list_display = (
        "nome",
        "getAtivoNome",
        "getUONome",
    )

    def getAtivoNome(self, obj):
        return obj.ativo.nome

    def getUONome(self, obj):
        return obj.ativo.uo.nome


admin.site.register(uep, uepAdmin)


class pocoAdmin(admin.ModelAdmin):
    model = poco
    search_fields = ("nome", "uep__nome")
    list_filter = (
        "uep__ativo__uo__nome",
        "uep__nome",
    )
    list_display = (
        "nome",
        "getUONome",
        "getUEPNome",
    )

    def getUEPNome(self, obj):
        return obj.uep.nome

    def getUONome(self, obj):
        return obj.uep.ativo.uo.nome


admin.site.register(poco, pocoAdmin)


class viAdmin(admin.ModelAdmin):
    model = variavel_industrial
    search_fields = ("poco__nome", "grandeza_industrial__nome")
    list_filter = ("grandeza_industrial__nome",)
    list_display = ("nome",)


admin.site.register(variavel_industrial, viAdmin)
admin.site.register(relacao_especialista_industrial)
admin.site.register(unidade_medida_padrao)
admin.site.register(unidade_medida)
